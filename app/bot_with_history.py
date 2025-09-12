# app/bot_with_history.py
from __future__ import annotations
from playwright.sync_api import sync_playwright, Error
import os, re, json, sqlite3, time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from .ai_client import generate_reply
from .rules import filter_and_fix
from .config import config

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "chat_brain.sqlite")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

START_URL = "https://viluu.de/mod99/chat/screen"

# --- KORREKTUR: JS_READ_HISTORY jetzt mit Zeitstempel ---
JS_READ_HISTORY = "() => { const cards = [...document.querySelectorAll('.messages-container .message-card')]; if (!cards.length) return []; function pickInfo(card) { const isMine = card.classList.contains('message-current'); const tsEl = card.querySelector('.message-date'); const tsText = tsEl ? (tsEl.innerText || '').trim() : null; const textEl = card.querySelector('.text'); const text = textEl ? textEl.innerText.trim() : ''; return { text, isMine, tsText }; } return cards.map(pickInfo); }"
JS_FILL_INPUT = "({value}) => { const ta = document.querySelector('#message-input'); if (!ta) return false; ta.value = value; ta.dispatchEvent(new Event('input', { bubbles: true })); return true; }"

def connect_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    return con
def bulk_save_messages(con: sqlite3.Connection, items: List[Dict[str, Any]]):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for m in items:
        text = (m.get("text") or "").strip()
        if not text: continue
        direction = "out" if m.get("isMine") else "in"
        ts_iso = parse_ts_to_iso(m.get("tsText"))
        con.execute("INSERT INTO messages(direction, text, created_at, ts) VALUES (?,?,?,?)", (direction, text, now, ts_iso))
    con.commit()

def parse_ts_to_iso(raw_ts: str | None) -> str | None:
    if not raw_ts: return None
    try:
        dt_obj = datetime.strptime(raw_ts, '%H:%M %d/%m/%Y')
        return dt_obj.isoformat()
    except (ValueError, TypeError):
        return datetime.now().isoformat() # Fallback auf aktuelle Zeit

def main(ki_provider: str):
    config.log_status("Starte Bot-Automatisierung...")
    config.log_debug(f"Debug-Level: {config.debug_level}, Polling-Intervall: {config.polling_interval}s")
    
    with sync_playwright() as p:
        print("Starte Chromium-Browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        login_url = "https://chatadmin.de/login"
        print(f"✅ Navigiere zur Login-Seite: {login_url}")
        page.goto(login_url)

        username = os.getenv("VILUU_USERNAME")
        password = os.getenv("VILUU_PASSWORD")

        if not username or not password:
            print("❌ Login-Daten nicht in .env gefunden.")
            browser.close()
            return
            
        config.log_debug("Fülle Login-Formular aus...")
        page.get_by_label("Nickname").fill(username)
        page.get_by_label("Password").fill(password)
        
        config.log_debug("Klicke auf den Login-Button...")
        page.get_by_role("button", name="Log In").click()
        
        # Allow automation to skip manual step if configured
        if config.auto_skip_manual:
            config.log_status("Auto-Skip aktiviert: Überspringe manuelle Navigation...")
            time.sleep(5)  # Give time for login to complete
            page.goto(START_URL)
            time.sleep(3)  # Allow page to load
        else:
            input("--> BITTE FÜHRE JETZT DIE MANUELLEN SCHRITTE AUS UND NAVIGIERE ZUM CHAT. DRÜCKE DANN HIER ENTER...")

        last_known_message_count = 0
        print("\n✅ Bot ist jetzt im Überwachungs- und Follow-Up-Modus...")
        print(f"   Polling-Intervall: {config.polling_interval}s | Follow-Up nach: {config.follow_up_hours}h")
        print("   Drücke Strg+C im Terminal, um den Bot zu beenden.")
        
        while True:
            try:
                config.log_verbose(f"Überprüfe Chat... (Nachrichten: {last_known_message_count})")
                history = page.evaluate(JS_READ_HISTORY)
                if not history:
                    config.log_debug("Kein Chat-Verlauf gefunden, warte...")
                    time.sleep(config.polling_interval)
                    continue

                current_message_count = len(history)
                latest_message = history[-1]
                
                config.log_verbose(f"Aktuelle Nachrichten: {current_message_count}, Letzte bekannt: {last_known_message_count}")
                
                # --- START: NEUE PROAKTIVE LOGIK ---
                
                # Szenario 1: Neue Nachricht vom Gegenüber (wie bisher)
                if current_message_count > last_known_message_count and not latest_message.get("isMine"):
                    
                    # --- START: NEUE PRÜFUNG AUF LEEREN TEXT (FIX) ---
                    incoming_text = (latest_message.get('text') or "").strip()
                    print(f"\n🔥 Neue Nachricht erkannt: '{incoming_text}'")
                    last_known_message_count = current_message_count

                    if incoming_text:
                        # Nur antworten, wenn der Text NICHT leer ist
                        config.log_status("Generiere Antwort auf neue Nachricht...")
                        generate_and_send_reply(page, ki_provider, history, latest_message)
                    else:
                        # Nachricht ist leer (z.B. Tipp-Indikator oder JS-SCRAPER FEHLER), ignoriere sie.
                        config.log_debug("JS-Scraper hat leere Nachricht gelesen. Ignoriere und warte auf echten Text.")
                    # --- ENDE: NEUE PRÜFUNG ---

                # Szenario 2: Follow-Up, wenn unsere letzte Nachricht unbeantwortet ist
                elif latest_message.get("isMine") and current_message_count == last_known_message_count:
                    last_message_time_iso = parse_ts_to_iso(latest_message.get("tsText"))
                    
                    if last_message_time_iso:
                        time_since_last_message = datetime.now() - datetime.fromisoformat(last_message_time_iso)
                        
                        if time_since_last_message > timedelta(hours=config.follow_up_hours):
                            print(f"\n⏰ Follow-Up Trigger: Deine letzte Nachricht ist über {config.follow_up_hours} Stunden alt. Generiere eine Follow-Up Nachricht.")
                            config.log_status("Sende Follow-Up Nachricht...")
                            generate_and_send_reply(page, ki_provider, history, None) 
                            last_known_message_count += 1 # Wichtig: Zähler erhöhen, um Spam zu verhindern
                
                else:
                    # Wenn keine neue Nachricht da ist, aktualisiere den Zähler für den nächsten Durchlauf
                    last_known_message_count = current_message_count

                config.log_verbose(f"Warte {config.polling_interval} Sekunden bis zur nächsten Überprüfung...")
                time.sleep(config.polling_interval)

            except KeyboardInterrupt:
                print("\nBot wird beendet.")
                browser.close()
                return
            except Exception as e:
                config.log_debug(f"Fehler aufgetreten: {type(e).__name__}: {e}")
                if config.debug_level >= 2:
                    import traceback
                    traceback.print_exc()
                print(f"⚠️ Ein Fehler ist aufgetreten: {e}. Prüfe in {config.polling_interval} Sekunden erneut.")
                time.sleep(config.polling_interval)

# --- NEUE FUNKTION, um Code-Wiederholung zu vermeiden ---
def generate_and_send_reply(page, ki_provider, history, latest_message):
    config.log_debug("Starte Antwort-Generierung...")
    
    con = connect_db()
    bulk_save_messages(con, history)
    con.close()
    config.log_debug("Verlauf in Datenbank gespeichert.")

    os.environ['KI_PROVIDER'] = ki_provider
    config.log_status(f"KI-Modus '{ki_provider}' aktiviert. Generiere Antwort...")
    
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12: tageszeit = "Morgen"
    elif 12 <= current_hour < 18: tageszeit = "Nachmittag"
    elif 18 <= current_hour < 22: tageszeit = "Abend"
    else: tageszeit = "Nacht"
    
    config.log_verbose(f"Tageszeit erkannt: {tageszeit}")
    
    # --- NEUER KONTEXT FÜR FOLLOW-UP ---
    if latest_message is None:
        # Dies ist ein proaktiver Follow-Up (Szenario 2)
        config.log_debug("Generiere Follow-Up Nachricht...")
        conversation_context = "Du hast vor einiger Zeit die letzte Nachricht geschrieben, aber keine Antwort erhalten. Schreibe jetzt eine kurze, freundliche und unaufdringliche Follow-Up Nachricht, um das Gespräch wieder anzustoßen (z.B. 'Hey, wollte nur mal kurz nachfragen, wie dein Tag so war 😊')."
        user_text = "" # Es gibt keine neue User-Nachricht
    else:
        # Dies ist eine direkte Antwort (Szenario 1)
        user_text = latest_message.get("text", "") # (Wir wissen dank der Prüfung oben, dass dieser Text nicht leer ist)
        is_new_conversation = len(history) <= 2
        if is_new_conversation:
            config.log_debug("Neue Unterhaltung erkannt.")
            conversation_context = "Dies ist die allererste Nachricht in einer neuen Unterhaltung."
        else:
            config.log_debug("Laufende Unterhaltung erkannt.")
            conversation_context = "Dies ist eine laufende Unterhaltung."

    # --- START: GENERISCHER MASTER PROMPT (FIX 3.0) ---
    # Schritt 1: Definiere die Persona und die Regeln (NEUTRAL, OHNE NAMEN)
    master_prompt_text = f"""
    DU BIST EINE MENSCHLICHE PERSON IN EINEM CHAT. VERHALTE DICH NATÜRLICH UND SEI KEINE MASCHINE.
    Dein Stil: Du bist charmant, witzig und führst ein natürliches, lockeres Gespräch. Du bist hier, um zu chatten und dein Gegenüber kennenzulernen.

    WICHTIGE REGELN (UNBEDINGT STRIKT EINHALTEN):
    1. NIEMALS TREFFEN: Lehne ALLE Anfragen nach realen Treffen (egal ob Kaffee, Spaziergang, Dates, "live sehen" oder Adressaustausch) immer höflich aber bestimmt ab. Sage, dass du dich wohler fühlst, wenn ihr erstmal nur hier schreibt.
    2. KEINE KONTAKTE: Teile NIEMALS Kontaktinformationen (kein WhatsApp, Instagram, Telegram, Telefonnummern, E-Mail etc.). Lehne dies ebenfalls höflich ab.
    3. STIL: Sprich immer in der "Du"-Form. Sei freundlich und interessiert, aber immer unverbindlich, was die reale Welt angeht. Antworte auf die Fragen, die dir gestellt werden.
    """

    # Schritt 2: Kombiniere den Master Prompt mit dem dynamischen Kontext
    system_rules = f"""
    {master_prompt_text}

    ZUSATZ-KONTEXT FÜR DIESE SPEZIFISCHE ANTWORT:
    - Aktuelle Tageszeit: Es ist gerade {tageszeit}.
    - Gesprächsstatus: {conversation_context}
    """
    # --- ENDE: GENERISCHER MASTER PROMPT ---
    
    config.log_verbose(f"Verwende letzten {min(10, len(history))} Nachrichten als Kontext")
    history_for_ai = [{'direction': 'out' if msg.get('isMine') else 'in', 'text': msg.get('text', '')} for msg in history[-10:]]
    
    config.log_debug("Rufe KI-API auf...")
    ai_reply = generate_reply(history_for_ai, system_rules, user_text)
    
    if ai_reply:
        config.log_status("KI-Antwort erhalten. Füge in Eingabefeld ein...")
        filtered, flags = filter_and_fix(ai_reply)
        page.evaluate(JS_FILL_INPUT, {"value": filtered})
        print("\n✅ Antwort in Eingabefeld eingefügt (NICHT gesendet):")
        print("   ", filtered)
        config.log_debug(f"Filter-Flags: {flags}")
    else:
        config.log_debug("KI konnte keine Antwort generieren.")
        print("⚠️ KI konnte keine Antwort generieren.")