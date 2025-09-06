# app/bot_read_history.py  (DEBUG/laut)
from __future__ import annotations
print("🔧 Start: bot_read_history.py geladen")

import json, re, sys, traceback
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, Error
    print("✅ Playwright importiert")
except Exception as e:
    print("❌ Playwright-Import fehlgeschlagen:", e)
    traceback.print_exc()
    sys.exit(1)

START_URL = "https://viluu.de/mod99/chat/screen"

JS_READ_HISTORY = r"""
(() => {
  const cards = [...document.querySelectorAll('.messages-container .message-card')];
  if (!cards.length) return JSON.stringify({ ok:false, reason:'no_messages' });

  function pickInfo(card) {
    const isMine = card.classList.contains('message-current');
    const tsRe = /\d{1,2}:\d{2}\s+\d{1,2}\/\d{1,2}\/\d{4}/;
    const lines = card.innerText.split('\n').map(s => s.trim()).filter(Boolean);
    const text = lines.filter(l => !tsRe.test(l)).join(' ').trim();

    let tsText = null;
    const cont = card.closest('.message-container') || card;
    const tsEl = cont.querySelector('.message-chat-bottom-date');
    if (tsEl) tsText = tsEl.innerText?.trim() || null;

    return { text, tsText, isMine };
  }

  const list = cards.map(pickInfo);
  return JSON.stringify({ ok:true, messages:list });
})();
"""

def parse_ts(ts_text: str) -> datetime | None:
    if not ts_text: return None
    m = re.search(r'(\d{1,2}):(\d{2})\s+(\d{1,2})/(\d{1,2})/(\d{4})', ts_text)
    if not m: return None
    hh, mm, dd, mo, yyyy = map(int, m.groups())
    try:
        return datetime(yyyy, mo, dd, hh, mm)
    except ValueError:
        return None

def main():
    print("🔧 main() gestartet")
    try:
        with sync_playwright() as p:
            print("🔧 Playwright Kontext erstellt")
            browser = p.chromium.launch(headless=False)
            print("✅ Chromium gestartet")
            page = browser.new_page()
            print("🔧 Neue Seite geöffnet")
            page.goto(START_URL)
            print("🌐 Seite geladen:", START_URL)

            print("✅ Chat-Seite geöffnet. Melde dich an und gehe zur Chat-Ansicht.")
            input("👉 Wenn du im Chat bist, drücke hier ENTER... ")

            try:
                print("⌛ warte auf DOM/Netz…")
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                page.wait_for_load_state("networkidle", timeout=20000)
                page.wait_for_selector(".messages-container", timeout=20000)
                page.wait_for_selector(".messages-container .message-card", timeout=20000)
                print("✅ Chat-Container & Cards gefunden")
            except Error as e:
                print("\n⚠️  Konnte keinen Nachrichtenbereich finden.")
                print("Fehler:", e)
                traceback.print_exc()
                input("ENTER zum Schließen…")
                browser.close()
                return

            result_json = None
            last_err = None
            for attempt in range(3):
                try:
                    print(f"🔧 Lese Verlauf… Versuch {attempt+1}/3")
                    result_json = page.evaluate(JS_READ_HISTORY)
                    break
                except Error as e:
                    last_err = e
                    print("⚠️ evaluate-Fehler, retry…", e)
                    page.wait_for_timeout(700)

            if result_json is None:
                print("\n🔴 Konnte Verlauf nicht auslesen.")
                print("Letzter Fehler:", last_err)
                traceback.print_exc()
                input("ENTER zum Schließen…")
                browser.close()
                return

            print("🔧 Ergebnis erhalten, parse JSON…")
            result = json.loads(result_json)
            if not result.get("ok"):
                print("\n🔴 Keine Nachrichten gefunden. Reason:", result.get("reason"))
                input("ENTER zum Schließen…")
                browser.close()
                return

            msgs = result["messages"] or []
            msgs = list(reversed(msgs))
            MAX_SHOW = 30
            shown = msgs[:MAX_SHOW]

            print(f"\n📜 Verlauf – letzte {min(len(shown), MAX_SHOW)} Nachrichten (neueste zuerst):\n")
            if not shown:
                print("   (leer)")
            else:
                for i, m in enumerate(shown, start=1):
                    who = "DU" if m.get("isMine") else "ER/SIE"
                    ts  = m.get("tsText") or "(ohne Zeit)"
                    txt = (m.get("text") or "").strip()
                    short = (txt[:140] + "…") if len(txt) > 140 else txt
                    print(f"{i:2d}) [{who}] {ts} — {short}")

            print("\nℹ️  Erklärung:")
            print("   • [DU] = deine Nachricht (rechte, weiße Blasen)")
            print("   • [ER/SIE] = Gegenüber (linke, farbige Blasen)")
            print("   • NUR Lesen – nichts wird gesendet.")

            input("\nFertig. ENTER zum Schließen…")
            browser.close()
    except Exception as e:
        print("💥 Unerwarteter Fehler in main():", e)
        traceback.print_exc()
        input("ENTER zum Schließen…")

if __name__ == "__main__":
    print("🔧 __main__ erreicht – starte main()")
    main()
