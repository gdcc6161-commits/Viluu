# app/rules.py
from __future__ import annotations
import re
from typing import Dict, Tuple, Optional

# ---------- Vorgaben ----------
MAX_LEN    = 500

# ---------- Regex ----------
RE_CONTACTS = re.compile(
    r"(whats\s*app|wa\b|telefon|handy|nummer|ruf an|anrufen|"
    r"telegram|tele?gram|snap(chat)?|instagram|insta|facebook|fb\b|"
    r"mail|e-?mail|email|gmail|yahoo|hotmail|outlook|icq|line|kik)",
    re.IGNORECASE
)

# --- START KORREKTUR: RE_MEETUP final erweitert ---
RE_MEETUP = re.compile(
    r"\b(uns treffen|dich treffen|treffen wir uns|date|verabred|reallife|real\s*life|"
    r"kaffee trinken|zum kaffee|auf einen kaffee|spazieren gehen|"
    r"sehen wir uns|wo treffen wir uns|wann treffen wir uns|wann und wo|"
    r"welcher ort|welche uhrzeit|hast du zeit|adresse|wo wohnst du|unternehmen|"
    r"was würdest du tun|was würdest du machen|ganz besonderes|nur wir beide|live sehen|"
    r"sieht man sich|begegnen|persönlich kennenlernen|persönlich vorstellen|vorbeikommen|"
    r"ellenlange schreiben|nie treffen|zufällig irgendwo)\b",
    re.IGNORECASE
)
# --- ENDE KORREKTUR ---

RE_LINK = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
RE_INCEST = re.compile(
    r"(?:^|\b)(inzest|stiefmutter|stiefvater|stiefschwester|stiefbruder|"
    r"bruder\b|schwester\b|vater\b|mutter\b)(?:\b|$)",
    re.IGNORECASE
)
RE_FAREWELL = re.compile(
    r"\b(tsch[uü]ss|ciao|auf wiedersehen|bye|gute nacht|bis bald|"
    r"mach[’']?s gut|schlaf gut|bis sp[aä]ter|bis dann)\b",
    re.IGNORECASE
)
RE_PUNCT_MULTI = re.compile(r"([!?.,;:]){2,}")
RE_SPACE_BEFORE_PUNCT = re.compile(r"\s+([!?.,;:])")
RE_MULTI_SPACE = re.compile(r"\s{2,}")
RE_ONLY_PUNCT = re.compile(r"^[\s,;:!?.\-–—]+$")

# ---------- Normalisierung ----------
def force_ss(text: str) -> str:
    return text.replace("ß", "ss").replace("ẞ", "SS")
def remove_dashes(text: str) -> str:
    return re.sub(r"[-–—]+", " ", text)
def basic_punctuation(text: str) -> str:
    out = RE_SPACE_BEFORE_PUNCT.sub(r"\1", text)
    out = RE_PUNCT_MULTI.sub(r"\1", out)
    out = RE_MULTI_SPACE.sub(" ", out).strip()
    if not out or RE_ONLY_PUNCT.match(out): return ""
    if out and out[-1] not in ".!?…":
        if out[-1].isalnum(): out += "."
    return out
def enforce_du_form(text: str) -> str:
    rules = [(r"\bSie\b", "du"),(r"\bIhnen\b", "dir"),(r"\bIhrer\b", "deiner"),(r"\bIhr\b", "dein"),(r"\bIhre\b", "deine"),(r"\bIhren\b", "deine"),]
    out = text
    for pat, rep in rules:
        out = re.sub(pat, rep, out)
    return out

# ---------- Pipeline-Durchlauf ----------
def _pipeline_once(raw: str) -> Tuple[str, Dict[str, bool], bool]:
    if RE_INCEST.search(raw or ""):
        sexual_triggers = re.compile(r"(ficken|sex|geil|ständer|muschi|pussy|schwanz|penis|vögeln|bumsen|lecken|lutschen|blasen)", re.IGNORECASE)
        if sexual_triggers.search(raw):
             return "", {"incest_block": True}, True

    flags: Dict[str, bool] = {"incest_block": False, "has_contacts": False,"has_meetup": False, "has_link": False, "had_farewell": False,"too_long": False, "used_du_form": False, "dash_removed": False,}
    txt = raw or ""
    
    if RE_MEETUP.search(txt):
        flags["has_meetup"] = True
        txt = "Ich finde unsere Gespräche hier wirklich spannend und möchte das gerne erstmal so beibehalten."
    if RE_CONTACTS.search(txt):
        flags["has_contacts"] = True
        txt = "Ich fühle mich am wohlsten, wenn wir uns vorerst nur hier im Chat austauschen."

    txt2 = force_ss(txt)
    before = txt2; txt2 = remove_dashes(txt2)
    if txt2 != before: flags["dash_removed"] = True
    before = txt2; txt2 = enforce_du_form(txt2)
    if txt2 != before: flags["used_du_form"] = True
    txt2 = basic_punctuation(txt2)

    if RE_LINK.search(txt2):
        flags["has_link"] = True
        txt2 = RE_LINK.sub("[Link entfernt]", txt2)
    if RE_FAREWELL.search(txt2):
        flags["had_farewell"] = True
        txt2 = RE_FAREWELL.sub("", txt2).strip()

    if len(txt2) > MAX_LEN:
        flags["too_long"] = True
        safe_cut = txt2[:MAX_LEN].rfind('.')
        if safe_cut > 0:
            txt2 = txt2[:safe_cut+1]
        else:
            txt2 = txt2[:MAX_LEN]

    if not txt2 or RE_ONLY_PUNCT.match(txt2):
        txt2 = "Erzähl mir bitte mehr, ich gehe darauf ein."

    violated = ("-" in txt2 or "–" in txt2 or "—" in txt2 or "ß" in txt2)
    return txt2, flags, violated

# ---------- Öffentliche API ----------
def filter_and_fix(raw_text: str) -> Tuple[str, Dict[str, bool]]:
    text = raw_text or ""
    combined_flags: Dict[str, bool] = {}
    for _ in range(3):
        text, flags, violated = _pipeline_once(text)
        for k, v in flags.items():
            combined_flags[k] = combined_flags.get(k, False) or bool(v)
        if not violated:
            break
    return text, combined_flags