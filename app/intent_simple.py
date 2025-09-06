# app/intent_simple.py
from __future__ import annotations
from typing import List, Dict

# --- Wortlisten (erweiterbar) ---------------------------------
BOUNDARY_WORDS = [
    "whatsapp", "nummer", "telefon", "anruf", "telegram", "snap", "instagram",
    "skype", "treffen", "date", "adresse", "mail", "e-mail", "email", "standort",
    "facebook", "signal", "videochat", "call"
]
SEXUAL_WORDS = [
    "sex", "küssen", "kuss", "geil", "lust", "blasen", "lecken", "69", "dirty",
    "nackt", "hard", "doggy", "oral", "anal", "titten", "brüste", "bruest", "busen",
    "verwöhnen", "verwoehnen", "vorlieben"
]
AGGRESSIVE_WORDS = [
    "dumm", "blöd", "blod", "verarschen", "verarsch", "spinnst", "scheiss", "scheiße", "arsch",
    "halt die", "idiot", "schlampe", "hure"
]
BIO_WORDS = [
    "cm", "kg", "groß", "gross", "größe", "groesse", "jahre", "alt", "alter",
    "kennenlernen", "kennen lernen", "möchten", "moechten", "möchte", "moechte"
]
HEALTH_WORDS = [
    "schlaganfall", "krank", "reha", "therapie", "belastung", "erschöpft", "müde", "muede", "stress"
]
PLACE_WORDS = ["lerchenberg", "mainz", "stadtteil", "stadt", "viertel", "bezirk"]

COMPLIMENT_WORDS = ["hübsch", "süss", "süß", "schön", "attraktiv", "engel", "toll", "wow"]
SMALLTALK_WORDS = ["hi", "hallo", "moin", "servus", "na ", "grüß", "gruss", "guten morgen", "guten abend"]

REPETITION_HINTS = ["wie gesagt", "nochmal", "noch mal", "hattest du", "vorhin", "bereits", "wieder"]

QUESTION_MARK = "?"

def _contains_any(text: str, words: List[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)

def _recent_contains(history: List[Dict], words: List[str], last_n: int = 6) -> bool:
    if not history:
        return False
    recent = history[-last_n:]
    joined = " || ".join((m.get("text") or "").lower() for m in recent)
    return any(w in joined for w in words)

def detect_intent(text: str, history: List[Dict]) -> str:
    """
    Liefert eine Intent-Kategorie für Templates:
      boundary, sexual, aggressive, repetition, smalltalk, compliment, question, fallback
    - Smalltalk wird VOR Frage priorisiert, wenn Begrüßungswörter vorkommen (auch mit '?').
    - Sexual kann auch über den jüngsten Verlauf erkannt werden (wenn der aktuelle Satz neutral ist).
    """
    t = (text or "").lower().strip()

    # 1) Harte Grenzen zuerst
    if _contains_any(t, BOUNDARY_WORDS):
        return "boundary"
    if _contains_any(t, AGGRESSIVE_WORDS):
        return "aggressive"

    # 2) Sexual (direkt ODER aus Verlauf)
    if _contains_any(t, SEXUAL_WORDS) or _recent_contains(history, SEXUAL_WORDS, last_n=6):
        return "sexual"

    # 3) Repetition (Hinweise im Satz ODER im Verlauf)
    if _contains_any(t, REPETITION_HINTS) or _recent_contains(history, REPETITION_HINTS, last_n=6):
        return "repetition"

    # 4) Smalltalk hat Vorrang vor "question"
    if _contains_any(t, SMALLTALK_WORDS):
        return "smalltalk"

    # 5) Kompliment
    if _contains_any(t, COMPLIMENT_WORDS):
        return "compliment"

    # 6) Frage?
    if QUESTION_MARK in t:
        return "question"

    # 7) Fallback
    return "fallback"
