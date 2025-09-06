# app/profile_extract.py
from __future__ import annotations
import os, re, sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "chat_brain.sqlite")

# -------------------------------------------------------
# Hilfen: DB
# -------------------------------------------------------
def connect_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def upsert_profile(con: sqlite3.Connection, side: str, **fields):
    # side in ('me','peer')
    cur = con.execute("SELECT id FROM profiles WHERE side=?", (side,))
    row = cur.fetchone()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if row:
        sets = []
        vals = []
        for k, v in fields.items():
            sets.append(f"{k}=?")
            vals.append(v)
        sets.append("updated_at=?")
        vals.append(now)
        vals.append(side)
        con.execute(f"UPDATE profiles SET {', '.join(sets)} WHERE side=?", vals)
    else:
        cols = ["side", "updated_at"] + list(fields.keys())
        vals = [side, now] + list(fields.values())
        qs   = ",".join(["?"] * len(vals))
        con.execute(f"INSERT INTO profiles ({', '.join(cols)}) VALUES ({qs})", vals)

def insert_dialog_info(con: sqlite3.Connection, key: str, value: str, confidence: float = 0.9):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    con.execute(
        "INSERT INTO dialog_info (key, value, confidence, created_at) VALUES (?,?,?,?)",
        (key, value, confidence, now)
    )

# -------------------------------------------------------
# Extraktions-Heuristiken (vorsichtig und streng)
# -------------------------------------------------------

# 1) Telefonnummer / Adresse – nur als „bekannt“ markieren (keine Speicherung!)
RE_PHONE = re.compile(r"\b(?:\+?\d{1,3}[\s/]?)?(?:\d{3,})\b")
RE_ADDRESS_HINT = re.compile(r"\b(strasse|straße|weg|platz|allee|hausnummer|plz)\b", re.IGNORECASE)

# 2) Stadt – nur, wenn es sehr typisch formuliert ist; sonst leer lassen
CITY_PATTERNS = [
    re.compile(r"\b(?:ich\s*(?:wohne|lebe)\s*(?:in|bei)|aus|komme\s*aus)\s+([A-ZÄÖÜ][a-zäöüß\-]{2,})\b"),
    re.compile(r"\b(?:wohnhaft\s*in)\s+([A-ZÄÖÜ][a-zäöüß\-]{2,})\b"),
]
# Wörter, die NIE Stadt sein können (um „allen“, „gut“ etc. auszuschließen)
CITY_BLACKLIST = {"allen", "alles", "gut", "bisschen", "heute", "morgen", "gestern"}

# 3) Beziehungstatus – einfache Muster
STATUS_MAP: Dict[str, str] = {
    r"\bsingle\b": "single",
    r"\bgeschieden\b": "geschieden",
    r"\bverheiratet\b": "verheiratet",
    r"\bgetrennt\b": "getrennt",
    r"\bverwitwet\b": "verwitwet",
}

# 4) Beruf – nur sehr konservativ (Schlüsselwörter)
JOB_HINT = re.compile(
    r"\b(ingenieur|mechaniker|handwerker|arzt|ärztin|pfleger|krankenschwester|fahrer|koch|köchin|"
    r"lehrer|lehrerin|student|studentin|it|informatiker|entwickler|programmierer|verk[aä]ufer|"
    r"friseur|friseurin|bauarbeiter|elektriker|anwalt|anwältin)\b",
    re.IGNORECASE
)

# 5) Gender – anhand von Selbstangaben (sehr vorsichtig)
GENDER_M = re.compile(r"\b(ich\s*bin\s*mann|m\s*\d{0,2}\b|\bmännlich\b)\b", re.IGNORECASE)
GENDER_F = re.compile(r"\b(ich\s*bin\s*frau|w\s*\d{0,2}\b|\bweiblich\b)\b", re.IGNORECASE)

# 6) Wünsche / Suche (Dialog-Info)
WISH_F_PLUS = re.compile(r"\b(freundschaft\s*plus|freundschaft\+|f\+)\b", re.IGNORECASE)
WISH_FEST   = re.compile(r"\b(etwas\s*festes|was\s*festes|beziehung|ernsthaft)\b", re.IGNORECASE)

# Inzest-/Familie – niemals speichern, niemals beantworten
RE_INCEST = re.compile(
    r"(inzest|stiefmutter|stiefvater|stiefschwester|stiefbruder|"
    r"\bschwester\b|\bbruder\b|\bmutter\b|\bvater\b|\btochter\b|\bsohn\b)",
    re.IGNORECASE
)

# „Treffen/Kontakte“ sollen keine Profilfelder auslösen
RE_CONTACT = re.compile(r"(whats\s*app|telefon|nummer|mail|email|instagram|telegram|snap)", re.IGNORECASE)
RE_MEETUP  = re.compile(r"(treffen|date|verabred|reallife|real\s*life|kaffee)", re.IGNORECASE)

def safe_city(text: str) -> Optional[str]:
    t = text.strip()
    for pat in CITY_PATTERNS:
        m = pat.search(t)
        if not m:
            continue
        city = m.group(1)
        low  = city.lower()
        if low in CITY_BLACKLIST:
            continue
        # Keine Wörter mit Apostroph, keine Verben
        if "'" in city or " " in city:
            continue
        # sieht wie Name aus (Großbuchstabe gefolgt von Kleinbuchstaben)
        if not re.match(r"^[A-ZÄÖÜ][a-zäöüß\-]{2,}$", city):
            continue
        return city
    return None

def extract_status(text: str) -> Optional[str]:
    tl = text.lower()
    for pat, value in STATUS_MAP.items():
        if re.search(pat, tl):
            # Dauer optional, z.B. "seit 3 jahren"
            m = re.search(r"seit\s*(\d{1,2})\s*(jahr|jahren)", tl)
            if m:
                n = m.group(1)
                return f"{value} seit {n} jahren"
            return value
    return None

def extract_job(text: str) -> Optional[str]:
    m = JOB_HINT.search(text)
    if m:
        return m.group(0).lower()
    return None

def extract_gender(text: str) -> Optional[str]:
    if GENDER_M.search(text):
        return "m"
    if GENDER_F.search(text):
        return "w"
    return None

def extract_wishes(text: str) -> list[Tuple[str, str]]:
    wishes = []
    if WISH_F_PLUS.search(text):
        wishes.append(("sucht", "freundschaft_plus"))
    if WISH_FEST.search(text):
        wishes.append(("sucht", "festes"))
    return wishes

def detect_phone_known(text: str) -> bool:
    # „bekannt“ markieren, wenn Zahlensequenzen wie Telefonnummern vorkommen,
    # aber keine Speicherung der Nummern!
    if RE_PHONE.search(text) and not RE_INCEST.search(text):
        return True
    return False

def detect_address_known(text: str) -> bool:
    return bool(RE_ADDRESS_HINT.search(text)) and not bool(RE_INCEST.search(text))

# -------------------------------------------------------
# Kernlogik
# -------------------------------------------------------
def scan_recent_messages(con: sqlite3.Connection, max_msgs: int = 40) -> list[str]:
    cur = con.execute(
        "SELECT text FROM messages ORDER BY id DESC LIMIT ?",
        (max_msgs,)
    )
    rows = cur.fetchall()
    # Neueste zuerst → wir verarbeiten absteigend
    return [r["text"] for r in rows if r["text"]]

def main():
    con = connect_db()
    try:
        texts = scan_recent_messages(con, max_msgs=60)
        if not texts:
            print("ℹ️  Keine Nachrichten in DB – nichts zu extrahieren.")
            return

        # Sammelcontainer
        city: Optional[str] = None
        status: Optional[str] = None
        job: Optional[str] = None
        gender: Optional[str] = None

        phone_known = False
        address_known = False
        wishes_pairs: list[Tuple[str,str]] = []

        # Streng: Inhalte mit Inzest oder Treffen/Kontakt nicht als Profil verwenden
        for t in texts:
            if RE_INCEST.search(t):
                continue
            if RE_CONTACT.search(t) or RE_MEETUP.search(t):
                # nur Dialog-Info ggf. (phone/address), aber keine Profilfelder
                if not phone_known and detect_phone_known(t):
                    phone_known = True
                if not address_known and detect_address_known(t):
                    address_known = True
                continue

            if city is None:
                c = safe_city(t)
                if c:
                    city = c

            if status is None:
                s = extract_status(t)
                if s:
                    status = s

            if job is None:
                j = extract_job(t)
                if j:
                    job = j

            if gender is None:
                g = extract_gender(t)
                if g:
                    gender = g

            # Wünsche (Dialog-Info)
            wishes_pairs.extend(extract_wishes(t))

        # In DB schreiben (nur was wir sicher haben)
        changed = False
        fields = {}
        if city:   fields["city"] = city; changed = True
        if status: fields["status"] = status; changed = True
        if job:    fields["job"] = job; changed = True
        if gender: fields["gender"] = gender; changed = True
        if changed:
            upsert_profile(con, side="peer", **fields)

        # Dialog-Infos eintragen
        if phone_known:
            insert_dialog_info(con, "telefonnummer", "bekannt", confidence=0.95)
        if address_known:
            insert_dialog_info(con, "adresse", "bekannt", confidence=0.90)
        for k, v in wishes_pairs:
            insert_dialog_info(con, k, v, confidence=0.85)

        con.commit()

        # Ausgabe
        print("✅ Profil- und Dialog-Infos aktualisiert.")
        # Profil zeigen
        cur = con.execute("SELECT side, name, city, status, job, gender, updated_at FROM profiles WHERE side='peer'")
        pr = cur.fetchone()
        if pr:
            print(f"   side={pr['side']}  city={pr['city'] or '-'}  status={pr['status'] or '-'}  job={pr['job'] or '-'}  gender={pr['gender'] or '-'}  updated={pr['updated_at']}")
        else:
            print("   peer-Profil: (noch leer)")

        # Dialog-Infos zeigen (nur letzte 10)
        cur = con.execute("SELECT key, value, confidence, created_at FROM dialog_info ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        if rows:
            print("   Dialog-Infos (neueste):")
            for r in rows:
                print(f"     - {r['key']} = {r['value']} (conf {r['confidence']:.2f}) {r['created_at']}")
        else:
            print("   Keine neuen Dialog-Infos.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
