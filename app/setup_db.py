# app/setup_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/chat_brain.sqlite")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

schema = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rules (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  pattern TEXT NOT NULL,        -- Regex (case-insensitive)
  action TEXT NOT NULL,         -- block | replace | rephrase
  replacement TEXT DEFAULT '',
  priority INTEGER DEFAULT 100  -- kleinere Zahl = wichtiger
);
"""

seed = [
  # Harte Richtlinien aus deinem Master (kurzer Start)
  ("NoMeetup",      r"(?i)(treffen|date|nummer|whats|telegram|snap|telefon|anruf|call)", "rephrase",
                    "Ich bleibe hier im Chat. Schreib mir, was dir wichtig ist, dann gehe ich darauf ein.", 5),
  ("EszettToSS",    r"ß", "replace", "ss", 10),
  ("NoHyphen",      r"-", "replace", " ", 10),
  ("TrimSpaces",    r"\s{2,}", "replace", " ", 90),
  # Du willst Umlaute behalten: deshalb KEINE Regel zu ä/ö/ü (wir lassen sie so!)
  # Länge 500 Zeichen erzwingen machen wir später im Code (einfacher und sicher).
]

def main():
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()
  cur.executescript(schema)
  cur.execute("DELETE FROM rules")  # sauber neu befüllen
  cur.executemany(
      "INSERT INTO rules (name, pattern, action, replacement, priority) VALUES (?,?,?,?,?)",
      seed
  )
  conn.commit()
  conn.close()
  print(f"✅ Datenbank erstellt: {DB_PATH} mit {len(seed)} Regeln.")

if __name__ == "__main__":
  main()
