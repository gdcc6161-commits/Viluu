# app/intent_selfcheck.py
from __future__ import annotations
from typing import List, Dict
from app.intent_simple import detect_intent

CASES: List[Dict] = [
    {
        "label": "Boundary: Nummer/WA/Meetup",
        "text": "Gib mir deine Nummer, lass uns auf WhatsApp schreiben oder treffen wir uns morgen?",
        "history": []
    },
    {
        "label": "Sexual: Vorlieben/Massage",
        "text": "Ich will dich küssen, magst du leidenschaftlich verwöhnen? Meine Vorlieben sind offen.",
        "history": []
    },
    {
        # Wichtig: hier bewusst neutraler Satz, aber der Verlauf ist sexuell -> soll 'sexual' werden
        "label": "Sexual: Verlauf deutet es an",
        "text": "Das kann ich dir aber noch nicht sagen.",
        "history": [
            {"text": "Beim Sex bin ich offen für alles, möchte vieles ausprobieren.", "isMine": False},
            {"text": "Du meinst leidenschaftlich verwöhnen, was magst du?", "isMine": True},
        ]
    },
    {
        "label": "Aggressiv",
        "text": "Bist du dumm oder was, verarsch mich nicht.",
        "history": []
    },
    {
        "label": "Frage",
        "text": "Magst du Hunde? Was ist deine Lieblingsserie?",
        "history": []
    },
    {
        "label": "Kompliment",
        "text": "Du bist so hübsch und attraktiv, wow.",
        "history": []
    },
    {
        # Begrüßung + Fragezeichen -> trotzdem smalltalk (Begrüßung hat Vorrang)
        "label": "Smalltalk",
        "text": "Hi, hallo, guten Abend, wie gehts?",
        "history": []
    },
    {
        "label": "Repetition: Verlauf",
        "text": "Wie gesagt, sag es mir nochmal.",
        "history": [
            {"text": "Kannst du mir das nochmal sagen?", "isMine": False},
            {"text": "Ich hab es dir vorhin schon geschrieben.", "isMine": True},
        ]
    },
    {
        "label": "Fallback",
        "text": "Ich war heute unterwegs und habe nachgedacht.",
        "history": []
    },
]

def main():
    print("Starte intent_selfcheck…\n")
    for i, c in enumerate(CASES, start=1):
        label = c["label"]
        text  = c["text"]
        hist  = c["history"]
        intent = detect_intent(text, hist)
        print(f"{i:02d}. [{label}]")
        print(f"    Eingabe : {text}")
        print(f"    Intent  : {intent}\n")
    print("✅ intent_selfcheck fertig.")

if __name__ == "__main__":
    main()

