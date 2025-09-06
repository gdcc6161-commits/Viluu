# app/db_migrate.py
from __future__ import annotations
import os, sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "chat_brain.sqlite")

NEEDED_PROFILE_COLS = {
    "name": "TEXT",
    "city": "TEXT",
    "status": "TEXT",            # unsere neue Kurzform (z. B. "single seit 3 jahren")
    "job": "TEXT",
    "gender": "TEXT",
    "updated_at": "TEXT",
}
# Manche Alt-DBs haben z. B. relationship_status / birthday – die lassen wir einfach stehen.

NEEDED_DIALOG_INFO_COLS = {
    "key": "TEXT",
    "value": "TEXT",
    "confidence": "REAL",
    "created_at": "TEXT",
}

def has_table(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,)
    )
    return cur.fetchone() is not None

def table_cols(con: sqlite3.Connection, name: str) -> set[str]:
    cur = con.execute(f"PRAGMA table_info({name})")
    return {row[1] for row in cur.fetchall()}  # row[1] = Spaltenname

def ensure_profiles(con: sqlite3.Connection):
    if not has_table(con, "profiles"):
        con.execute("""
        CREATE TABLE profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            side TEXT,         -- 'me' oder 'peer'
            name TEXT,
            city TEXT,
            status TEXT,
            job TEXT,
            gender TEXT,
            updated_at TEXT
        )
        """)
        print("🆕 Tabelle 'profiles' neu erstellt.")
        return

    existing = table_cols(con, "profiles")
    for col, ctype in NEEDED_PROFILE_COLS.items():
        if col not in existing:
            con.execute(f"ALTER TABLE profiles ADD COLUMN {col} {ctype}")
            print(f"🔧 Spalte hinzugefügt: profiles.{col} ({ctype})")

def ensure_dialog_info(con: sqlite3.Connection):
    if not has_table(con, "dialog_info"):
        con.execute("""
        CREATE TABLE dialog_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT,
            confidence REAL,
            created_at TEXT
        )
        """)
        print("🆕 Tabelle 'dialog_info' neu erstellt.")
        return

    existing = table_cols(con, "dialog_info")
    for col, ctype in NEEDED_DIALOG_INFO_COLS.items():
        if col not in existing:
            con.execute(f"ALTER TABLE dialog_info ADD COLUMN {col} {ctype}")
            print(f"🔧 Spalte hinzugefügt: dialog_info.{col} ({ctype})")

def main():
    print(f"🔗 DB: {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    try:
        ensure_profiles(con)
        ensure_dialog_info(con)
        con.commit()

        # Übersicht
        prof_cols = ", ".join(sorted(table_cols(con, "profiles")))
        di_cols   = ", ".join(sorted(table_cols(con, "dialog_info")))
        print("📋 profiles-Spalten:", prof_cols)
        print("📋 dialog_info-Spalten:", di_cols)
        print("✅ Migration fertig.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
