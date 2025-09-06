# app/db_check.py
from __future__ import annotations
import os, sqlite3, textwrap
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "chat_brain.sqlite")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def fmt(s: str | None, n: int = 100) -> str:
    if not s:
        return ""
    s = " ".join(s.split())
    return (s[: n - 1] + "…") if len(s) > n else s

def safe_print(msg: str = ""):
    print(msg, flush=True)

def show_header(title: str):
    safe_print("\n" + "=" * 60)
    safe_print(title)
    safe_print("=" * 60)

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB nicht gefunden: {DB_PATH}")
        return

    con = connect()
    cur = con.cursor()

    # 1) Kurze Übersicht
    show_header("ÜBERSICHT")
    cur.execute("SELECT COUNT(*) FROM messages")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM messages WHERE direction='in'")
    cnt_in = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM messages WHERE direction='out'")
    cnt_out = cur.fetchone()[0]
    safe_print(f"Nachrichten gesamt : {total}")
    safe_print(f"  eingehend (in)   : {cnt_in}")
    safe_print(f"  ausgehend (out)  : {cnt_out}")

    # 2) Letzte eingehende + ausgehende Zeitstempel
    cur.execute("SELECT ts, raw_ts FROM messages WHERE direction='in'  AND ts IS NOT NULL ORDER BY ts DESC LIMIT 1")
    last_in  = cur.fetchone()
    cur.execute("SELECT ts, raw_ts FROM messages WHERE direction='out' AND ts IS NOT NULL ORDER BY ts DESC LIMIT 1")
    last_out = cur.fetchone()

    def parse_iso(row):
        if not row or not row["ts"]:
            return None
        try:
            return datetime.strptime(row["ts"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    tin  = parse_iso(last_in)
    tout = parse_iso(last_out)

    safe_print("\nLetzte Zeitstempel:")
    safe_print(f"  Eingehend : {last_in['raw_ts'] if last_in else '-'}  → {last_in['ts'] if last_in else '-'}")
    safe_print(f"  Ausgehend : {last_out['raw_ts'] if last_out else '-'} → {last_out['ts'] if last_out else '-'}")

    if tin and tout:
        gap_h = abs((tin - tout).total_seconds()) / 3600.0
        safe_print(f"  Lücke     : {gap_h:.1f} Stunden")

    # 3) Letzte 10 Nachrichten (neueste zuerst)
    show_header("LETZTE 10 NACHRICHTEN (neueste zuerst)")
    cur.execute("""
        SELECT id, direction, ts, raw_ts, text
        FROM messages
        ORDER BY COALESCE(ts, created_at) DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    if not rows:
        safe_print("(keine Einträge)")
    else:
        for r in rows:
            who = "DU" if r["direction"] == "out" else "ER/SIE"
            ts  = r["raw_ts"] or r["ts"] or "-"
            txt = fmt(r["text"], 140)
            safe_print(f"[{who}] {ts} — {txt}")

    # 4) Profile + Dialog-Infos
    show_header("PROFILE")
    cur.execute("SELECT id, side, IFNULL(name,'') AS name, IFNULL(city,'') AS city, IFNULL(relationship_status,'') AS rs, IFNULL(job,'') AS job, IFNULL(updated_at,'') AS up FROM profiles ORDER BY side")
    profs = cur.fetchall()
    if not profs:
        safe_print("(noch keine Profileinträge)")
    else:
        for p in profs:
            safe_print(f"- side={p['side']} id={p['id']}  name='{p['name']}'  city='{p['city']}'  status='{p['rs']}'  job='{p['job']}'  updated={p['up']}")

    show_header("DIALOG-INFO")
    cur.execute("""
        SELECT d.profile_id, p.side, d.key, d.value, d.updated_at
        FROM dialog_info d
        LEFT JOIN profiles p ON p.id = d.profile_id
        ORDER BY d.updated_at DESC
        LIMIT 20
    """)
    infos = cur.fetchall()
    if not infos:
        safe_print("(noch keine Dialog-Infos)")
    else:
        for i in infos:
            safe_print(f"[{i['side'] or '?'}] {i['key']} → {i['value']} (zu Profil {i['profile_id']}, {i['updated_at']})")

    con.close()
    safe_print("\n✅ Fertig.")

if __name__ == "__main__":
    main()
