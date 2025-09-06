# app/extend_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/chat_brain.sqlite")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    # 1) Gesetze (nie brechen)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS laws (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      description TEXT NOT NULL
    )
    """)
    laws = [
        ("GermanOnly", "Nur Deutsch, saubere Rechtschreibung und Satzzeichen."),
        ("NoAutoSend", "Nie automatisch senden. Nur in das Eingabefeld schreiben."),
        ("MaxLen500", "Antwort maximal 500 Zeichen."),
        ("UmlautsKeep", "Umlaute ä ö ü beibehalten."),
        ("EszettToSS", "ß immer zu ss umschreiben."),
        ("NoHyphen", "Keine Bindestriche im Text."),
        ("NoMeetup", "Nie Treffen oder Date vorschlagen oder annehmen."),
        ("NoPlatforms", "Kein Plattformwechsel oder Kontaktdaten anfragen oder geben."),
        ("OnTopic", "Immer Bezug auf den Verlauf und die aktuelle Nachricht."),
    ]
    cur.executemany("INSERT OR IGNORE INTO laws (name, description) VALUES (?,?)", laws)

    # 2) Intents
    cur.execute("""
    CREATE TABLE IF NOT EXISTS intents (
      id INTEGER PRIMARY KEY,
      code TEXT NOT NULL UNIQUE,
      description TEXT NOT NULL
    )
    """)
    intents = [
        ("sexual",     "sexuell direkt"),
        ("compliment", "Kompliment / Anziehung"),
        ("question",   "Frage"),
        ("smalltalk",  "neutrales Kennenlernen"),
        ("boundary",   "Grenzen und Regeln ansprechen"),
        ("repetition", "Thema wurde schon besprochen"),
        ("aggressive", "angriff oder Beschimpfung"),
        ("sadness",    "traurigkeit, erschöpfung, klage"),
        ("fallback",   "keine klare Absicht")
    ]
    cur.executemany("INSERT OR IGNORE INTO intents (code, description) VALUES (?,?)", intents)

    # 3) Templates (mehrere Varianten je Intent für Abwechslung)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS templates (
      id INTEGER PRIMARY KEY,
      intent_code TEXT NOT NULL REFERENCES intents(code),
      gender TEXT NOT NULL DEFAULT 'neutral',   -- male | female | neutral
      tone TEXT NOT NULL DEFAULT 'warm',        -- warm | frech | sachlich | empathisch
      body TEXT NOT NULL,
      max_len INTEGER NOT NULL DEFAULT 500
    )
    """)
    t = []
    # sexual (ohne Treffen, nur Chat)
    t += [("sexual","neutral","warm","Du klingst sehr direkt. Was reizt dich hier im Chat gerade am meisten?"),
          ("sexual","neutral","empathisch","Deine Nachricht ist sehr direkt. Was genau wünschst du dir hier im Chat?"),
          ("sexual","neutral","sachlich","Ich bleibe hier im Chat. Was möchtest du hier gerade am liebsten erleben?")]
    # compliment
    t += [("compliment","neutral","warm","Danke für das Kompliment. Was gefällt dir an mir besonders?"),
          ("compliment","neutral","empathisch","Danke dir. Was genau spricht dich an?"),
          ("compliment","neutral","frech","Nettes Kompliment. Was magst du am meisten an mir?")]
    # question
    t += [("question","neutral","sachlich","Gute Frage. Was ist dir daran am wichtigsten?"),
          ("question","neutral","warm","Spannende Frage. Was erwartest du dir davon?"),
          ("question","neutral","empathisch","Gute Frage. Was wäre dir in der Sache am wichtigsten?")]
    # smalltalk
    t += [("smalltalk","neutral","warm","Erzähl mir ein wenig mehr über dich, dann kann ich besser anknüpfen."),
          ("smalltalk","neutral","empathisch","Ich bin neugierig. Was macht dich im Moment am meisten aus?"),
          ("smalltalk","neutral","frech","Dann mal los. Was sollte ich als Erstes über dich wissen?")]
    # boundary
    t += [("boundary","neutral","klar","Ich bleibe hier im Chat. Schreib mir, was dir wichtig ist, dann gehe ich darauf ein."),
          ("boundary","neutral","sachlich","Wir bleiben im Chat. Was ist dir inhaltlich wichtig?"),
          ("boundary","neutral","warm","Hier im Chat fühle ich mich wohl. Worum geht es dir gerade am meisten?")]
    # repetition
    t += [("repetition","neutral","sachlich","Darüber haben wir schon gesprochen. Was ist seitdem neu für dich?"),
          ("repetition","neutral","warm","Das Thema hatten wir vorhin schon. Was hat sich für dich verändert?"),
          ("repetition","neutral","empathisch","Wir waren bei dem Punkt schon einmal. Was fehlt dir dazu noch?")]
    # aggressive
    t += [("aggressive","neutral","klar","Ich möchte respektvoll bleiben. Worum geht es dir inhaltlich?"),
          ("aggressive","neutral","sachlich","Lass uns respektvoll bleiben. Was genau stört dich?"),
          ("aggressive","neutral","empathisch","Ich höre dich. Formulieren wir es ruhig, was genau ist dein Punkt?")]
    # sadness
    t += [("sadness","neutral","empathisch","Das klingt schwer. Was würde dir gerade gut tun?"),
          ("sadness","neutral","warm","Ich nehme dich ernst. Was brauchst du im Moment am meisten?"),
          ("sadness","neutral","sachlich","Verstanden. Wobei wünschst du dir hier im Chat Unterstützung?")]
    # fallback
    t += [("fallback","neutral","warm","Klingt interessant. Woran denkst du gerade hier im Chat?"),
          ("fallback","neutral","sachlich","Erzähl mir mehr, damit ich gezielt antworten kann."),
          ("fallback","neutral","empathisch","Ich bin ganz Ohr. Was ist dir gerade wichtig?")]
    cur.executemany(
        "INSERT INTO templates (intent_code,gender,tone,body,max_len) VALUES (?,?,?,?,500)", t
    )

    # 4) Gefühllexikon (ausgewaehlte Tokens, erweiterbar)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feelings_lex (
      id INTEGER PRIMARY KEY,
      category TEXT NOT NULL,   -- traurig, erschöpft, ängstlich, ärger, frustriert, hoffnungsvoll, dankbar, froh, stark, positiv, unsicher
      token TEXT NOT NULL
    )
    """)
    lex = [
      # traurig
      ("traurig","traurig"),("traurig","trauer"),("traurig","depressiv"),
      ("traurig","verzweifelt"),("traurig","deprimiert"),("traurig","niedergeschlagen"),
      # erschöpft
      ("erschöpft","müde"),("erschöpft","erschöpft"),("erschöpft","ausgelaugt"),("erschöpft","kaputt"),
      # ängstlich
      ("ängstlich","angst"),("ängstlich","ängstlich"),("ängstlich","besorgt"),("ängstlich","unsicher"),
      # ärger
      ("ärger","wütend"),("ärger","sauer"),("ärger","verärgert"),("ärger","genervt"),
      # frustriert
      ("frustriert","frustriert"),("frustriert","enttäuscht"),("frustriert","hilflos"),
      # hoffnungsvoll
      ("hoffnungsvoll","hoffnungsvoll"),("hoffnungsvoll","zuversichtlich"),("hoffnungsvoll","optimistisch"),
      # dankbar
      ("dankbar","dankbar"),("dankbar","danke"),
      # froh
      ("froh","glücklich"),("froh","zufrieden"),("froh","happy"),("froh","erleichtert"),
      # stark
      ("stark","stark"),("stark","mutig"),("stark","tapfer"),
      # positiv
      ("positiv","gut"),("positiv","super"),("positiv","toll"),("positiv","prima"),
      # unsicher
      ("unsicher","unsicher"),("unsicher","zweifel"),("unsicher","ratlos"),
    ]
    cur.executemany("INSERT INTO feelings_lex (category, token) VALUES (?,?)", lex)

    conn.commit()
    conn.close()
    print("✅ DB erweitert: laws, intents, templates, feelings_lex.")

if __name__ == "__main__":
    run()
