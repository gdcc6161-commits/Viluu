# app/bot_with_history.py
from __future__ import annotations
from playwright.sync_api import sync_playwright, Error, TimeoutError as PlaywrightTimeoutError
import os, re, json, sqlite3, time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from .ai_client import generate_reply
from .rules import filter_and_fix
from .logger import logger, log_browser_action, log_message_processing

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
    """Verbindet zur SQLite-Datenbank."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("PRAGMA foreign_keys = ON;")
        logger.info("Datenbankverbindung hergestellt")
        return con
    except Exception as e:
        logger.error("Fehler bei Datenbankverbindung", e)
        raise

def bulk_save_messages(con: sqlite3.Connection, items: List[Dict[str, Any]]):
    """Speichert Nachrichten in die Datenbank."""
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        saved_count = 0
        
        for m in items:
            text = (m.get("text") or "").strip()
            if not text: 
                continue
                
            direction = "out" if m.get("isMine") else "in"
            ts_iso = parse_ts_to_iso(m.get("tsText"))
            con.execute("INSERT INTO messages(direction, text, created_at, ts) VALUES (?,?,?,?)", 
                       (direction, text, now, ts_iso))
            saved_count += 1
            
        con.commit()
        log_message_processing("gespeichert", saved_count)
        
    except Exception as e:
        logger.error("Fehler beim Speichern der Nachrichten", e)
        con.rollback()

def parse_ts_to_iso(raw_ts: str | None) -> str | None:
    """Konvertiert Zeitstempel zu ISO-Format."""
    if not raw_ts: 
        return None
    try:
        dt_obj = datetime.strptime(raw_ts, '%H:%M %d/%m/%Y')
        return dt_obj.isoformat()
    except (ValueError, TypeError):
        return datetime.now().isoformat() # Fallback auf aktuelle Zeit

def safe_browser_operation(operation_name: str, operation_func, max_retries: int = 2):
    """
    Führt Browser-Operationen mit Fehlerbehandlung durch.
    
    Args:
        operation_name: Name der Operation für Logging
        operation_func: Funktion die ausgeführt werden soll
        max_retries: Maximale Anzahl der Wiederholungsversuche
    
    Returns:
        Ergebnis der Operation oder None bei Fehler
    """
    for attempt in range(max_retries + 1):
        try:
            result = operation_func()
            log_browser_action(f"{operation_name} erfolgreich", True)
            return result
        except PlaywrightTimeoutError as e:
            if attempt == max_retries:
                logger.error(f"Browser-Operation '{operation_name}' nach {max_retries + 1} Versuchen fehlgeschlagen (Timeout)", e)
                log_browser_action(f"{operation_name} fehlgeschlagen (Timeout)", False)
                return None
            logger.warning(f"Timeout bei '{operation_name}' (Versuch {attempt + 1}), warte 5s...")
            time.sleep(5)
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Browser-Operation '{operation_name}' nach {max_retries + 1} Versuchen fehlgeschlagen", e)
                log_browser_action(f"{operation_name} fehlgeschlagen", False)
                return None
            logger.warning(f"Fehler bei '{operation_name}' (Versuch {attempt + 1}): {e}")
            time.sleep(3)
    
    return None

def main(ki_provider: str):
    """Hauptfunktion des Bots."""
    logger.info(f"Bot-Start mit KI-Provider: {ki_provider}")
    
    with sync_playwright() as p:
        try:
            logger.info("Starte Chromium-Browser...")
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Login-Prozess
            login_url = "https://chatadmin.de/login"
            logger.info(f"Navigiere zur Login-Seite: {login_url}")
            
            def navigate_to_login():
                page.goto(login_url, timeout=30000)
                return True
            
            if not safe_browser_operation("Navigation zu Login-Seite", navigate_to_login):
                logger.error("Konnte nicht zur Login-Seite navigieren")
                browser.close()
                return

            username = os.getenv("VILUU_USERNAME")
            password = os.getenv("VILUU_PASSWORD")

            if not username or not password:
                logger.error("Login-Daten nicht in .env gefunden")
                print("❌ Login-Daten nicht in .env gefunden.")
                browser.close()
                return
                
            logger.info("Fülle Login-Formular aus...")
            
            def fill_login_form():
                page.get_by_label("Nickname").fill(username)
                page.get_by_label("Password").fill(password)
                return True
            
            def click_login_button():
                page.get_by_role("button", name="Log In").click()
                return True
            
            if not safe_browser_operation("Login-Formular ausfüllen", fill_login_form):
                logger.error("Konnte Login-Formular nicht ausfüllen")
                browser.close()
                return
                
            if not safe_browser_operation("Login-Button klicken", click_login_button):
                logger.error("Konnte Login-Button nicht klicken")
                browser.close()
                return
            
            logger.info("Login erfolgreich, warte auf manuelle Navigation zum Chat...")
            print("\n" + "="*60)
            print("✅ LOGIN ERFOLGREICH!")
            print("📍 NÄCHSTE SCHRITTE:")
            print("   1. Navigiere manuell zum Chat-Bereich in deinem Browser")
            print("   2. Öffne die gewünschte Unterhaltung")
            print("   3. Komme dann hierher zurück und drücke ENTER")
            print("="*60)
            input("➤ Drücke ENTER wenn du im Chat bist und der Bot starten soll...")

            last_known_message_count = 0
            logger.info("Bot startet Überwachungs- und Antwort-Modus...")
            print("\n✅ Bot ist jetzt aktiv und überwacht den Chat...")
            print("   💡 Drücke Strg+C im Terminal, um den Bot zu beenden.")
            print("   📊 Überprüfung alle 15 Sekunden...")
            
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            while True:
                try:
                    def read_chat_history():
                        return page.evaluate(JS_READ_HISTORY)
                    
                    history = safe_browser_operation("Chat-Verlauf lesen", read_chat_history)
                    
                    if history is None:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(f"Zu viele aufeinanderfolgende Fehler ({consecutive_errors}), beende Bot")
                            break
                        logger.warning(f"Konnte Chat-Verlauf nicht lesen (Fehler {consecutive_errors}/{max_consecutive_errors})")
                        time.sleep(30)  # Längere Pause bei Fehlern
                        continue
                    
                    consecutive_errors = 0  # Reset bei erfolgreichem Lesen
                    
                    if not history:
                        time.sleep(15)
                        continue

                    current_message_count = len(history)
                    latest_message = history[-1]
                    
                    # --- START: NEUE PROAKTIVE LOGIK ---
                    
                    # Szenario 1: Neue Nachricht vom Gegenüber (wie bisher)
                    if current_message_count > last_known_message_count and not latest_message.get("isMine"):
                        
                        incoming_text = (latest_message.get('text') or "").strip()
                        logger.info(f"Neue Nachricht erkannt: '{incoming_text[:50]}{'...' if len(incoming_text) > 50 else ''}'")
                        last_known_message_count = current_message_count

                        if incoming_text:
                            generate_and_send_reply(page, ki_provider, history, latest_message)
                        else:
                            logger.warning("Leere Nachricht erkannt, ignoriere sie")

                    # Szenario 2: Follow-Up, wenn unsere letzte Nachricht unbeantwortet ist
                    elif latest_message.get("isMine") and current_message_count == last_known_message_count:
                        last_message_time_iso = parse_ts_to_iso(latest_message.get("tsText"))
                        
                        if last_message_time_iso:
                            time_since_last_message = datetime.now() - datetime.fromisoformat(last_message_time_iso)
                            
                            if time_since_last_message > timedelta(hours=4):
                                logger.info("Follow-Up Trigger: Letzte Nachricht ist über 4 Stunden alt")
                                generate_and_send_reply(page, ki_provider, history, None) 
                                last_known_message_count += 1
                    
                    else:
                        last_known_message_count = current_message_count

                    time.sleep(15)

                except KeyboardInterrupt:
                    logger.info("Bot wird durch Benutzer beendet (Ctrl+C)")
                    print("\n👋 Bot wird beendet...")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Unerwarteter Fehler im Hauptloop (Fehler {consecutive_errors}/{max_consecutive_errors})", e)
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Zu viele aufeinanderfolgende Fehler, beende Bot")
                        break
                        
                    print(f"⚠️ Ein Fehler ist aufgetreten: {e}")
                    print(f"   Prüfe in 30 Sekunden erneut... (Fehler {consecutive_errors}/{max_consecutive_errors})")
                    time.sleep(30)

        except Exception as e:
            logger.error("Kritischer Fehler beim Browser-Start", e)
            print(f"❌ Kritischer Fehler: {e}")
        finally:
            try:
                browser.close()
                logger.info("Browser geschlossen")
            except:
                pass

# --- NEUE FUNKTION, um Code-Wiederholung zu vermeiden ---
def generate_and_send_reply(page, ki_provider, history, latest_message):
    """Generiert und sendet eine Antwort."""
    try:
        con = connect_db()
        bulk_save_messages(con, history)
        con.close()

        os.environ['KI_PROVIDER'] = ki_provider
        logger.info(f"Generiere Antwort mit KI-Provider: {ki_provider}")
        
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12: tageszeit = "Morgen"
        elif 12 <= current_hour < 18: tageszeit = "Nachmittag"
        elif 18 <= current_hour < 22: tageszeit = "Abend"
        else: tageszeit = "Nacht"
        
        # --- NEUER KONTEXT FÜR FOLLOW-UP ---
        if latest_message is None:
            conversation_context = "Du hast vor einiger Zeit die letzte Nachricht geschrieben, aber keine Antwort erhalten. Schreibe jetzt eine kurze, freundliche und unaufdringliche Follow-Up Nachricht, um das Gespräch wieder anzustoßen (z.B. 'Hey, wollte nur mal kurz nachfragen, wie dein Tag so war 😊')."
            user_text = ""
        else:
            user_text = latest_message.get("text", "")
            is_new_conversation = len(history) <= 2
            if is_new_conversation:
                conversation_context = "Dies ist die allererste Nachricht in einer neuen Unterhaltung."
            else:
                conversation_context = "Dies ist eine laufende Unterhaltung."

        # --- START: GENERISCHER MASTER PROMPT (FIX 3.0) ---
        master_prompt_text = f"""
        DU BIST EINE MENSCHLICHE PERSON IN EINEM CHAT. VERHALTE DICH NATÜRLICH UND SEI KEINE MASCHINE.
        Dein Stil: Du bist charmant, witzig und führst ein natürliches, lockeres Gespräch. Du bist hier, um zu chatten und dein Gegenüber kennenzulernen.

        WICHTIGE REGELN (UNBEDINGT STRIKT EINHALTEN):
        1. NIEMALS TREFFEN: Lehne ALLE Anfragen nach realen Treffen (egal ob Kaffee, Spaziergang, Dates, "live sehen" oder Adressaustausch) immer höflich aber bestimmt ab. Sage, dass du dich wohler fühlst, wenn ihr erstmal nur hier schreibt.
        2. KEINE KONTAKTE: Teile NIEMALS Kontaktinformationen (kein WhatsApp, Instagram, Telegram, Telefonnummern, E-Mail etc.). Lehne dies ebenfalls höflich ab.
        3. STIL: Sprich immer in der "Du"-Form. Sei freundlich und interessiert, aber immer unverbindlich, was die reale Welt angeht. Antworte auf die Fragen, die dir gestellt werden.
        """

        system_rules = f"""
        {master_prompt_text}

        ZUSATZ-KONTEXT FÜR DIESE SPEZIFISCHE ANTWORT:
        - Aktuelle Tageszeit: Es ist gerade {tageszeit}.
        - Gesprächsstatus: {conversation_context}
        """
        
        history_for_ai = [{'direction': 'out' if msg.get('isMine') else 'in', 'text': msg.get('text', '')} for msg in history[-10:]]
        ai_reply = generate_reply(history_for_ai, system_rules, user_text)
        
        if ai_reply:
            logger.success("KI-Antwort erhalten")
            filtered, flags = filter_and_fix(ai_reply)
            
            def fill_input_field():
                return page.evaluate(JS_FILL_INPUT, {"value": filtered})
            
            if safe_browser_operation("Antwort in Eingabefeld einfügen", fill_input_field):
                logger.success("Antwort erfolgreich eingefügt")
                print(f"\n✅ Antwort eingefügt (NICHT automatisch gesendet):")
                print(f"   💬 {filtered}")
                print(f"   🏷️  Flags: {flags}")
            else:
                logger.error("Konnte Antwort nicht in Eingabefeld einfügen")
        else:
            logger.warning("KI konnte keine Antwort generieren")
            print("⚠️ KI konnte keine Antwort generieren.")
            
    except Exception as e:
        logger.error("Fehler beim Generieren und Senden der Antwort", e)
        print(f"❌ Fehler beim Generieren der Antwort: {e}")