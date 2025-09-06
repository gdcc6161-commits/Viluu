# app/db_write.py
from __future__ import annotations
import os, re, json, glob
from datetime import datetime
import sqlite3
from typing import List, Dict, Any, Tuple, Union

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH   = os.path.join(BASE_DIR, "chat_brain.sqlite")
LOG_DIR   = os.path.join(BASE_DIR, "logs")

# ---------- helpers ----------

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def parse_ts(raw_ts: str) -> str | None:
    if not raw_ts:
        return None
    m = re.search(r'(\d{1,2}):(\d{2})\s+(\d{1,2})/(\d{1,2})/(\d{4})', raw_ts)
    if not m:
        return None
    hh, mm, dd, mo, yy = map(int, m.groups())
    try:
        dt = datetime(yy, mo, dd, hh, mm, 0)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def latest_history_json() -> str | None:
    files = sorted(glob.glob(os.path.join(LOG_DIR, "history_*.json")))
    return files[-1] if files else None

# ---------- Profile ----------

def upsert_profile(conn: sqlite3.Connection, side: str, **fields) -> int:
    row = conn.execute("SELECT id FROM profiles WHERE side=?", (side,)).fetchone()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO profiles(side, updated_at) VALUES (?,?)", (side, now))
    return cur.lastrowid

# ---------- Messages speichern ----------

def save_message(conn: sqlite3.Connection,
                 direction: str, text: str, raw_ts: str | None,
                 peer_name: str | None = None, conv_id: str | None = None):
    iso_ts = parse_ts(raw_ts) if raw_ts else None
    now    = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO messages(conv_id, direction, text, ts, raw_ts, peer_name, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (conv_id, direction, text, iso_ts, raw_ts, peer_name, now)
    )

def bulk_save_from_history(conn: sqlite3.Connection, history: Union[Dict[str, Any], List[Any]], conv_id: str | None = None) -> int:
    """
    Akzeptiert:
      1) Dict mit "messages"
      2) direkte Liste von Nachrichten
    """
    if isinstance(history, list):
        msgs = history
    elif isinstance(history, dict) and "messages" in history:
        msgs = history.get("messages") or []
    else:
        msgs = []

    count = 0
    for m in msgs:
        if not isinstance(m, dict):
            continue
        text    = (m.get("text") or "").strip()
        raw_ts  = m.get("tsText") or None
        is_mine = bool(m.get("isMine"))
        direction = "out" if is_mine else "in"
        save_message(conn, direction, text, raw_ts, peer_name=None, conv_id=conv_id)
        count += 1
    return count

# ---------- CLI ----------

def load_json_file(path: str) -> Union[Dict[str, Any], List[Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cli():
    print(f"🔗 DB: {DB_PATH}")
    latest = latest_history_json()
    if not latest:
        print("❌ Kein history_*.json in logs/ gefunden. Bitte zuerst bot_with_history laufen lassen.")
        return
    print(f"📄 Neuste History-Datei: {latest}")

    data = load_json_file(latest)

    conn = connect()
    try:
        me_id   = upsert_profile(conn, "me")
        peer_id = upsert_profile(conn, "peer")

        n = bulk_save_from_history(conn, data, conv_id=None)
        conn.commit()
        print(f"✅ {n} Nachrichten in die DB übernommen.")
        print("   Tabelle: messages")
    finally:
        conn.close()

if __name__ == "__main__":
    cli()
