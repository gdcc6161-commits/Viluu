# app/rules_selfcheck.py
from app.rules import filter_and_fix  # NICHT ändern

tests = [
    # Kontakte/Meetup/Links -> müssen abgewehrt werden
    "Schreib mir auf WhatsApp 0176-123456, dann treffen wir uns: https://example.com",
    # Umlaute aus ae/oe/ue + keine Bindestriche + ss statt ß
    "Ich bin muede und aeusserst erschoepft... koennen wir spaeter schreiben?",
    # Abschiedsfloskel entfernen, Dialog weiterführen
    "Gute Nacht, bis spaeter!",
    # Treffen andeuten -> klare Absage muss rein
    "Hast du Lust auf ein Date oder Kaffee trinken?",
    # Inzest/Familie -> hart blockieren (keine Antwort erzeugen)
    "Das Thema Stiefschwester moechte ich ansprechen.",
]

print("Starte Rules-Selbsttest...\n")
for i, t in enumerate(tests, 1):
    out, flags = filter_and_fix(t, gap_hours=25)  # 25h simuliert die >24h-Regel
    print(f"--- Test {i} ---")
    print("IN :", t)
    print("OUT:", out)
    print("FLG:", flags)
    print()

print("✅ rules_selfcheck: fertig.")
