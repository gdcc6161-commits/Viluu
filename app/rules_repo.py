# app/rules_repo.py
import re
import sqlite3
import random
from pathlib import Path

DB_PATH = Path("data/chat_brain.sqlite")

class RuleEngine:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def apply_rules(self, text: str) -> str:
        """ wendet Regeln in richtiger Reihenfolge an """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM rules ORDER BY priority ASC")
        rules = cur.fetchall()
        t = text
        for r in rules:
            pattern, action, repl = r["pattern"], r["action"], r["replacement"]
            if action == "replace":
                t = re.sub(pattern, repl, t)
            elif action == "rephrase":
                # block/rephrase = wir geben Ersatztext zurück
                if re.search(pattern, t):
                    t = repl
        # harte Grenze: max 500 Zeichen
        if len(t) > 500:
            t = t[:497] + "..."
        return t.strip()

    def pick_template(self, intent_code: str) -> str:
        """ wählt zufällige Vorlage für Intent """
        cur = self.conn.cursor()
        cur.execute("SELECT body FROM templates WHERE intent_code=? ORDER BY RANDOM() LIMIT 1", (intent_code,))
        row = cur.fetchone()
        return row["body"] if row else "[Keine Vorlage gefunden]"

    def detect_feeling(self, text: str) -> list[str]:
        """ erkennt Stimmungskategorien im Text """
        cur = self.conn.cursor()
        cur.execute("SELECT category, token FROM feelings_lex")
        rows = cur.fetchall()
        found = []
        for row in rows:
            if row["token"].lower() in text.lower():
                found.append(row["category"])
        return sorted(set(found))

if __name__ == "__main__":
    eng = RuleEngine()
    demo = "Hey, lass uns ein Treffen machen 😏 – ich bin müde und erschöpft."
    print("📥 Eingabe:", demo)
    out = eng.apply_rules(demo)
    print("📤 Nach Regeln:", out)
    print("💡 Vorlage sexual:", eng.pick_template("sexual"))
    print("😊 Gefühle:", eng.detect_feeling(demo))
