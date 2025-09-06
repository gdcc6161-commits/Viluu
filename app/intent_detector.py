# app/intent_detector.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class IntentResult:
    intent: str                 # z.B. 'question', 'compliment', 'sexual', ...
    labels: List[str]           # zusätzliche Tags ('boundary', 'aggressive', 'repetition' ...)
    confidence: float           # 0..1 grobe Sicherheit
    matched: List[str]          # getroffene Schlüsselwörter/Pfade

# Stichwort-Listen (deutsch, kleinschreibung)
KW = {
    "boundary": [
        "treffen", "date", "nummer", "whatsapp", "telegram", "snap", "telefon", "anrufen",
        "adresse", "standort", "wo wohnst", "woher genau", "videochat", "cam", "skype"
    ],
    "aggressive": [
        "dumm", "halt die", "spinnst", "verarsch", "hure", "arsch", "fotze", "idiot", "scheiss"
    ],
    "sexual": [
        "sex", "ficken", "blasen", "lecken", "69", "hart", "doggy", "anal", "brüste", "bruste",
        "titten", "geil", "bett", "knutschen", "kuss", "küssen", "kuscheln", "oral"
    ],
    "compliment": [
        "süß", "suess", "hübsch", "huebsch", "schön", "schoen", "attraktiv", "heiss", "heiß",
        "mag dich", "gefällst", "gefaellst", "gefällt", "gefaellt", "wow", "traum", "wunderschön"
    ],
    "smalltalk": [
        "hi", "hallo", "hey", "wie geht", "na", "guten morgen", "guten tag", "guten abend", "moin",
        "was machst", "alles gut", "wie läufts", "wie laeufts"
    ],
    "repetition": [
        "schon gesagt", "bereits besprochen", "hatten wir", "wie vorhin", "nochmal", "wieder", "zum x-ten mal"
    ],
}

QUESTION_RE = re.compile(r"\?\s*$|^warum|^wieso|^wie|^was|^wann|^wo|^welch", re.I)

# Priorität: zuerst harte Grenzen/Angriffe, dann Emotion/Content, dann generisch
PRIORITY = ["boundary", "aggressive", "sexual", "compliment", "question", "repetition", "smalltalk", "fallback"]

def _hits(text: str, keys: List[str]) -> List[str]:
    t = text.lower()
    hits = []
    for k in keys:
        if k in t:
            hits.append(k)
    return hits

def detect_intent(text: str, recent_context: str = "") -> IntentResult:
    """
    Regelbasierte Intent-Erkennung mit klarer Priorität.
    recent_context: optional kurzer Verlauf (für 'repetition').
    """
    if not text or not text.strip():
        return IntentResult("fallback", [], 0.2, [])

    t = text.lower().strip()
    labels: List[str] = []
    matched: List[str] = []

    # Boundary / aggressive haben Vorrang
    b = _hits(t, KW["boundary"])
    if b:
        matched += b
        return IntentResult("boundary", ["boundary"], 0.95, matched)

    a = _hits(t, KW["aggressive"])
    if a:
        matched += a
        return IntentResult("aggressive", ["aggressive"], 0.9, matched)

    # Frage?
    is_question = bool(QUESTION_RE.search(t))

    # Sexual / Compliment / Smalltalk / Repetition
    sx = _hits(t, KW["sexual"])
    if sx: matched += sx
    cp = _hits(t, KW["compliment"])
    if cp: matched += cp
    st = _hits(t, KW["smalltalk"])
    if st: matched += st

    rep = False
    if recent_context:
        for k in KW["repetition"]:
            if k in t or k in recent_context.lower():
                rep = True
                matched.append(k)
                break

    # Priorisierte Auswahl
    if sx:
        return IntentResult("sexual", labels, 0.85, matched)
    if cp:
        return IntentResult("compliment", labels, 0.8, matched)
    if is_question:
        return IntentResult("question", labels, 0.75, matched)
    if rep:
        return IntentResult("repetition", labels, 0.7, matched)
    if st:
        return IntentResult("smalltalk", labels, 0.7, matched)

    return IntentResult("fallback", labels, 0.4, matched)

# Mini-Demo
if __name__ == "__main__":
    tests = [
        "Hast du WhatsApp? Treffen wir uns?",
        "Du bist wirklich hübsch!",
        "Wie groß bist du?",
        "Na, alles gut bei dir?",
        "Blasen oder lecken – was magst du?",
        "Das hatten wir doch schon gesagt.",
        "Ok"
    ]
    for s in tests:
        r = detect_intent(s)
        print(f"{s} -> {r.intent} ({r.confidence:.2f}) hits={r.matched}")
