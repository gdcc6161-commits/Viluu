import os
import requests
import google.generativeai as genai
import time
from colorama import Fore, Style
from typing import Optional, List, Dict, Any
from .logger import logger, log_ai_request, log_error_with_retry


# --- HILFSFUNKTION FÜR KONSOLEN-AUSGABEN ---
def print_ai_info(message):
    """Gibt eine formatierte Info-Nachricht auf der Konsole aus."""
    print(f"{Fore.CYAN}[AI-CLIENT]{Style.RESET_ALL} {message}")

def print_ai_error(message):
    """Gibt eine formatierte Fehler-Nachricht auf der Konsole aus."""
    print(f"{Fore.RED}[AI-CLIENT FEHLER]{Style.RESET_ALL} {message}")


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Führt eine Funktion mit exponential backoff retry aus.
    
    Args:
        func: Funktion die ausgeführt werden soll
        max_retries: Maximale Anzahl von Wiederholungsversuchen
        base_delay: Basis-Verzögerung zwischen Versuchen
        
    Returns:
        Das Ergebnis der Funktion oder None bei Fehler
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Alle {max_retries + 1} Versuche fehlgeschlagen", e)
                return None
            
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            log_error_with_retry(str(e), attempt + 1, max_retries + 1)
            print_ai_error(f"Versuch {attempt + 1} fehlgeschlagen, warte {delay:.1f}s...")
            time.sleep(delay)
    
    return None


# --- KI-PROVIDER: LOKALES MODELL (z.B. Kobold) ---
def generate_reply_local(history, system_rules, user_message):
    """
    Generiert eine Antwort über eine lokale API (kompatibel mit Kobold).
    """
    endpoint = os.getenv("KOBOLD_ENDPOINT", "http://127.0.0.1:5001/api/v1/generate")
    
    def make_request():
        prompt = f"{system_rules}\n\n"
        prompt += "--- CHAT-VERLAUF ---\n"
        for msg in history[-5:]:
            role = "user" if msg['direction'] == 'in' else "model"
            prompt += f"{role}: {msg['text']}\n"
        prompt += f"--- AKTUELLE NACHRICHT ---\n"
        prompt += f"user: {user_message}\n"
        prompt += "model:"

        payload = {
            'prompt': prompt,
            'max_new_tokens': 250,
            'temperature': 0.8,
            'top_p': 0.9,
            'repetition_penalty': 1.1,
            'stop_sequence': ["\nuser:", "\nmodel:"]
        }
        
        print_ai_info(f"Sende Anfrage an lokales Modell via {endpoint}...")
        start_time = time.time()
        
        response = requests.post(endpoint, json=payload, timeout=180)
        response.raise_for_status()
        
        result_text = response.json()['results'][0]['text']
        clean_text = result_text.strip()
        
        response_time = time.time() - start_time
        log_ai_request("kobold", True, response_time)
        print_ai_info("Antwort vom lokalen Modell erhalten.")
        return clean_text
    
    return retry_with_backoff(make_request, max_retries=2, base_delay=2.0)


# --- KI-PROVIDER: GEMINI (Google) ---
def generate_reply_gemini(history, system_rules, user_message):
    """
    Generiert eine Antwort über die Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_ai_error("GEMINI_API_KEY nicht gefunden. Bitte in der .env Datei setzen.")
        log_ai_request("gemini", False)
        return None

    def make_request():
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        gemini_history = []
        for msg in history:
            role = "user" if msg['direction'] == 'in' else "model"
            gemini_history.append({'role': role, 'parts': [msg['text']]})

        full_prompt = f"{system_rules}\n\n--- LETZTE NACHRICHT ---\n{user_message}"

        print_ai_info("Sende Anfrage an Gemini API...")
        start_time = time.time()
        
        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(full_prompt)
        
        clean_text = response.text.strip()
        
        response_time = time.time() - start_time
        log_ai_request("gemini", True, response_time)
        print_ai_info("Antwort von Gemini erhalten.")
        return clean_text
    
    return retry_with_backoff(make_request, max_retries=3, base_delay=1.0)


# --- HAUPTFUNKTION, DIE ALLES STEUERT ---
def generate_reply(history, system_rules, user_message):
    """
    Hauptfunktion: Wählt den KI-Provider basierend auf der Konfiguration
    und generiert eine Antwort.
    """
    provider = os.getenv("KI_PROVIDER", "kobold").lower()

    logger.info(f"Generiere Antwort mit {provider.upper()}")
    
    start_time = time.time()
    result = None
    
    if provider == "gemini":
        result = generate_reply_gemini(history, system_rules, user_message)
    elif provider == "kobold":
        result = generate_reply_local(history, system_rules, user_message)
    else:
        error_msg = f"Unbekannter KI_PROVIDER '{provider}' in der Konfiguration."
        print_ai_error(error_msg)
        logger.error(error_msg)
        log_ai_request(provider, False)
        return None
    
    if result is None:
        log_ai_request(provider, False)
        print_ai_error("Konnte keine Antwort generieren. Alle Versuche fehlgeschlagen.")
    
    return result