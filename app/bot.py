# app/bot.py
from __future__ import annotations
from playwright.sync_api import sync_playwright, Error
import json, re
from datetime import datetime

# unsere Module
from intent_detector import detect_intent
from templates import (
    pick_template, pick_pause_lead,
    normalize_text, enforce_rules
)

# ---- Einstellungen ----
START_URL = "https://viluu.de/mod99/chat/screen"

# ---- Browser-JS: Nachrichten lesen (eingehend/ausgehend + Zeit) ----
JS_READ_LAST_BOTH = r"""
(() => {
  const cards = [...document.querySelectorAll('.messages-container .message-card')];
  if (!cards.length) return JSON.stringify({ ok:false, reason:'no_messages' });

  function pickInfo(card) {
    const tsRe = /\d{1,2}:\d{2}\s+\d{1,2}\/\d{1,2}\/\d{4}/;
    const lines = card.innerText.split('\n').map(s => s.trim()).filter(Boolean);
    const text = lines.filter(l => !tsRe.test(l)).join(' ').trim();

    let tsText = null;
    const cont = card.closest('.message-container') || card;
    const tsEl = cont.querySelector('.message-chat-bottom-date');
    if (tsEl) tsText = tsEl.innerText?.trim() || null;

    return { text, tsText };
  }

  const outgoing = cards.filter(c => c.classList.contains('message-current')); // deine
  const incoming = cards.filter(c => !c.classList.contains('message-current')); // gegenüber

  const last_out = outgoing.at(-1) ? pickInfo(outgoing.at(-1)) : null;
  const last_in  = incoming.at(-1) ? pickInfo(incoming.at(-1)) : null;

  return JSON.stringify({ ok:true, last_in, last_out });
})();
"""

# ---- Browser-JS: Text ins Eingabefeld schreiben (nicht senden) ----
JS_WRITE_INPUT = r"""
(text) => {
  const ta = document.querySelector('textarea#message-input');
  if (!ta) return false;
  ta.value = text;
  ta.dispatchEvent(new Event('input', {bubbles: true}));
  return true;
}
"""

# ---- Hilfsfunktionen ----
def parse_ts(ts_text: str) -> datetime | None:
    """Parst '19:57 22/8/2025' zu datetime."""
    if not ts_text:
        return None
    m = re.search(r'(\d{1,2}):(\d{2})\s+(\d{1,2})/(\d{1,2})/(\d{4})', ts_text)
    if not m:
        return None
    hh, mm, dd, mo, yyyy = map(int, m.groups())
    try:
        return datetime(yyyy, mo, dd, hh, mm)
    except ValueError:
        return None

def pick_greeting(now: datetime, msg_time: datetime | None) -> str:
    """Zeitabhängige Begrüßung (bei altem Thread neutraler)."""
    if msg_time:
        diff_hours = abs((now - msg_time).total_seconds()) / 3600.0
        if diff_hours > 6:  # bei langer Lücke neutral
            return "Hey"
    hour = now.hour
    if 5 <= hour < 10:   return "Guten Morgen"
    if 10 <= hour < 17:  return "Guten Tag"
    if 17 <= hour < 22:  return "Guten Abend"
    return "Hey"

def classify_gap_lead(last_out: datetime | None, last_in: datetime | None, now: datetime) -> str:
    """Grob einschätzen, ob wir einen kleinen 'Lead-In' brauchen (long/mid/short)."""
    if last_out:
        ref = last_in or now
        hrs = (ref - last_out).total_seconds() / 3600.0
        if hrs > 24: return "long"
        if hrs > 2:  return "mid"
        return "short"
    return "short"

def compose_reply(intent: str, greet: str, gap_kind: str) -> str:
    """Antworttext aus Bausteinen erzeugen + Regeln anwenden."""
    lead = pick_pause_lead(gap_kind)
    body = pick_template(intent)
    reply = f"{greet}! {lead}{body}".strip()
    reply = normalize_text(reply)
    reply = enforce_rules(reply)
    return reply

# ---- Hauptprogramm ----
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(START_URL)

        print("✅ Chat-Seite geöffnet. Melde dich an und gehe zur Chat-Ansicht.")
        input("👉 Wenn du im Chat bist, drücke hier ENTER... ")

        # 1) Auf stabilen Chat warten
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=20000)
        except Error:
            pass  # nicht kritisch

        try:
            page.wait_for_selector(".messages-container", timeout=20000)
            page.wait_for_selector(".messages-container .message-card", timeout=20000)
        except Error:
            print("\n⚠️  Konnte keinen Nachrichtenbereich finden. Bist du sicher in der Chat-Ansicht?")
            input("ENTER zum Schließen...")
            browser.close()
            return

        # 2) Nachrichten auslesen (mit Retry, falls Auto-Reload)
        result_json = None
        last_err = None
        for attempt in range(3):
            try:
                result_json = page.evaluate(JS_READ_LAST_BOTH)
                break
            except Error as e:
                last_err = e
                page.wait_for_timeout(700)  # kurz warten und erneut

        if result_json is None:
            print("\n🔴 Konnte Nachrichten nicht auslesen (mehrfacher Reload?).")
            print("   Tipp: Nach dem Login kurz warten, dann ENTER drücken –")
            print("        oder die Seite mit F5 aktualisieren und wieder ENTER.")
            print(f"   Letzter Fehler: {last_err}")
            input("\nENTER zum Schließen...")
            browser.close()
            return

        result = json.loads(result_json)
        if not result.get("ok"):
            print("\n🔴 Keine Nachrichten gefunden.")
            input("\nENTER zum Schließen...")
            browser.close()
            return

        last_in  = result.get("last_in")
        last_out = result.get("last_out")

        in_time  = parse_ts(last_in["tsText"])  if last_in  else None
        out_time = parse_ts(last_out["tsText"]) if last_out else None

        now = datetime.now()
        greet    = pick_greeting(now, in_time or out_time)
        gap_kind = classify_gap_lead(out_time, in_time, now)

        print("\n🟢 Letzte eingehende Nachricht:")
        if last_in:
            print("   Text :", last_in['text'] or "(leer)")
            print("   Zeit :", last_in['tsText'], "→", in_time if in_time else "(nicht erkannt)")
        else:
            print("   (keine)")

        print("\n🔵 Deine letzte (ausgehende) Nachricht:")
        if last_out:
            print("   Text :", last_out['text'] or "(leer)")
            print("   Zeit :", last_out['tsText'], "→", out_time if out_time else "(nicht erkannt)")
        else:
            print("   (keine)")

        gap_info = "–"
        if in_time and out_time:
            hrs = (in_time - out_time).total_seconds() / 3600.0
            gap_info = f"{hrs:.1f} Stunden zwischen deiner letzten Nachricht und seiner/ihrer Antwort"
        elif in_time and not out_time:
            gap_info = "Keine eigene Vor-Nachricht gefunden"
        print("\n⏱️  Gap:", gap_info)
        print("👋 Begrüßungsvorschlag:", greet)
        print("🧩 Gap-Kategorie:", gap_kind)

        # 3) Intent erkennen
        incoming_text  = last_in['text']  if last_in  else ""
        recent_context = last_out['text'] if last_out else ""
        intent_res = detect_intent(incoming_text, recent_context=recent_context)

        print("\n🧭 Intent-Erkennung:")
        print(f"   Intent      : {intent_res.intent}  (conf {intent_res.confidence:.2f})")
        print(f"   Schlüssel   : {', '.join(intent_res.matched) if intent_res.matched else '-'}")

        # 4) Antwort bauen & nur ins Eingabefeld schreiben
        draft = compose_reply(intent_res.intent, greet, gap_kind)
        ok = page.evaluate(JS_WRITE_INPUT, draft)
        if ok:
            print("\n✍️ Vorschlag ins Eingabefeld geschrieben (NICHT gesendet):")
            print("   ", draft)
        else:
            print("\n⚠️  Konnte das Eingabefeld nicht finden.")

        input("\nFertig. ENTER zum Schließen...")
        browser.close()

if __name__ == "__main__":
    main()
