# app/upgrade_db.py
import sqlite3, os, json, datetime as dt

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_brain.sqlite")

DDL = [
    # Profile der beiden Seiten (du & Gegenüber)
    """
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        side TEXT NOT NULL CHECK(side IN ('me','peer')),
        name TEXT,
        gender TEXT,           -- 'm','w','d' o.ä.
        city TEXT,
        relationship_status TEXT,
        birthday TEXT,         -- ISO 'YYYY-MM-DD' oder frei
        job TEXT,
        updated_at TEXT
    );
    """,

    # Freie Dialog-Infos als Key/Value
    """
    CREATE TABLE IF NOT EXISTS dialog_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        key TEXT NOT NULL,
        value TEXT,
        updated_at TEXT,
        UNIQUE(profile_id, key),
        FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    );
    """,

    # Nachrichten-Archiv (alles, was wir lesen/schreiben)
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conv_id TEXT,                -- optionaler Dialogschlüssel
        direction TEXT NOT NULL CHECK(direction IN ('in','out')),
        text TEXT NOT NULL,
        ts TEXT,                     -- ISO 'YYYY-MM-DD HH:MM:SS'
        raw_ts TEXT,                 -- der gelesene „19:57 22/8/2025“-Stempel
        peer_name TEXT,
        created_at TEXT
    );
    """,

    # Harte Regeln (Verbote / Aktionen)
    """
    CREATE TABLE IF NOT EXISTS rules_hard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pattern TEXT NOT NULL,   -- Regex
        action TEXT NOT NULL,    -- 'block' | 'replace'
        replace_with TEXT,       -- falls action='replace'
        enabled INTEGER NOT NULL DEFAULT 1
    );
    """,

    # Normalisierungen (Soft-Replacements)
    """
    CREATE TABLE IF NOT EXISTS normalize_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        find TEXT NOT NULL,
        repl TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1
    );
    """,

    # Allgemeine Einstellungen
    """
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """,

    # Log, wenn eine Regel gegriffen hat (zur Kontrolle)
    """
    CREATE TABLE IF NOT EXISTS rule_violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER,
        when_ts TEXT,
        sample TEXT,
        fixed TEXT,
        FOREIGN KEY(rule_id) REFERENCES rules_hard(id)
    );
    """,

    # Indizes
    "CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);",
    "CREATE INDEX IF NOT EXISTS idx_messages_dir ON messages(direction);",
    "CREATE INDEX IF NOT EXISTS idx_dialog_info_k ON dialog_info(key);"
]

SEED_RULES = [
    # Kontakt-/Treffen-Verbote
    dict(name="no_contacts",
         pattern=r"(whats\s*app|telefon|nummer|handy|snap|instagram|insta|telegram)",
         action="block", replace_with=None, enabled=1),
    dict(name="no_meetup",
         pattern=r"(treffen|date|verabreden|real\s*life)",
         action="block", replace_with=None, enabled=1),
]

SEED_NORMALIZE = [
    # Bindestriche/Em-Dash entfernen → Leerzeichen
    dict(find=r"[-–—]+", repl=" "),
    # Mehrfache Leerzeichen auf eines
    dict(find=r"\s{2,}", repl=" "),
]

SEED_SETTINGS = {
    "max_len": "500",               # harte Grenze
    "answer_target_len": "420",     # Ziel, damit mit Signoff < 500 bleibt
    "greeting_mode": "smart"        # keine Zwangs-Begrüßung
}

def ensure_conn():
    if not os.path.exists(DB_PATH):
        print(f"ℹ️  DB wird neu angelegt: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def upsert_settings(conn, kv):
    for k, v in kv.items():
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
            (k, v)
        )

def seed_rules(conn):
    # harte Regeln nur hinzufügen, wenn gleicher name noch nicht existiert
    cur = conn.execute("SELECT name FROM rules_hard;")
    existing = {r[0] for r in cur.fetchall()}
    for r in SEED_RULES:
        if r["name"] in existing:
            continue
        conn.execute(
            "INSERT INTO rules_hard(name,pattern,action,replace_with,enabled) "
            "VALUES (?,?,?,?,?)",
            (r["name"], r["pattern"], r["action"], r["replace_with"], r["enabled"])
        )

def seed_normalize(conn):
    cur = conn.execute("SELECT find,repl FROM normalize_map;")
    existing = {(a,b) for a,b in cur.fetchall()}
    for n in SEED_NORMALIZE:
        tup = (n["find"], n["repl"])
        if tup in existing:
            continue
        conn.execute(
            "INSERT INTO normalize_map(find,repl,enabled) VALUES (?,?,1)",
            tup
        )

def main():
    conn = ensure_conn()
    try:
        for stmt in DDL:
            conn.execute(stmt)

        upsert_settings(conn, SEED_SETTINGS)
        seed_rules(conn)
        seed_normalize(conn)

        conn.commit()
        print("✅ DB-Upgrade erfolgreich.")
        print(f"   Datei: {DB_PATH}")
        print("   Tabellen: profiles, dialog_info, messages, rules_hard, normalize_map, settings, rule_violations")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
