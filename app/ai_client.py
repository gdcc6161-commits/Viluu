import os
import requests
import google.generativeai as genai
from colorama import Fore, Style

# --- HILFSFUNKTION FÜR KONSOLEN-AUSGABEN ---
def print_ai_info(message):
    """Gibt eine formatierte Info-Nachricht auf der Konsole aus."""
    print(f"{Fore.CYAN}[AI-CLIENT]{Style.RESET_ALL} {message}")

def print_ai_error(message):
    """Gibt eine formatierte Fehler-Nachricht auf der Konsole aus."""
    print(f"{Fore.RED}[AI-CLIENT FEHLER]{Style.RESET_ALL} {message}")

# --- KI-PROVIDER: LOKALES MODELL (z.B. Kobold) ---
def generate_reply_local(history, system_rules, user_message):
    """
    Generiert eine Antwort über eine lokale API (kompatibel mit Kobold).
    """
    endpoint = os.getenv("KOBOLD_ENDPOINT", "http://127.0.0.1:5001/api/v1/generate")
    
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
        'max_new_tokens': 250, # Mehr Tokens für längere Antworten
        'temperature': 0.8,
        'top_p': 0.9,
        'repetition_penalty': 1.1,
        'stop_sequence': ["\nuser:", "\nmodel:"]
    }
    
    print_ai_info(f"Sende Anfrage an lokales Modell via {endpoint}...")
    try:
        # --- HIER IST DIE ÄNDERUNG: Die Wartezeit wurde auf 180 Sekunden erhöht ---
        response = requests.post(endpoint, json=payload, timeout=180)
        
        response.raise_for_status()
        
        result_text = response.json()['results'][0]['text']
        clean_text = result_text.strip()
        
        print_ai_info("Antwort vom lokalen Modell erhalten.")
        return clean_text
    except requests.exceptions.RequestException as e:
        print_ai_error(f"Verbindung zum lokalen Modell fehlgeschlagen: {e}")
        return None
    except Exception as e:
        print_ai_error(f"Unerwarteter Fehler bei der Abfrage des lokalen Modells: {e}")
        return None

# --- KI-PROVIDER: GEMINI (Google) ---
def generate_reply_gemini(history, system_rules, user_message):
    """
    Generiert eine Antwort über die Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_ai_error("GEMINI_API_KEY nicht gefunden. Bitte in der .env Datei setzen.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        print_ai_error(f"Fehler bei der Konfiguration des Gemini-Modells: {e}")
        return None

    gemini_history = []
    for msg in history:
        role = "user" if msg['direction'] == 'in' else "model"
        gemini_history.append({'role': role, 'parts': [msg['text']]})

    full_prompt = f"{system_rules}\n\n--- LETZTE NACHRICHT ---\n{user_message}"

    print_ai_info("Sende Anfrage an Gemini API...")
    try:
        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(full_prompt)
        
        clean_text = response.text.strip()
        
        print_ai_info("Antwort von Gemini erhalten.")
        return clean_text
    except Exception as e:
        print_ai_error(f"Fehler bei der Abfrage der Gemini API: {e}")
        return None

# --- HAUPTFUNKTION, DIE ALLES STEUERT ---
def generate_reply(history, system_rules, user_message):
    """
    Hauptfunktion: Wählt den KI-Provider basierend auf der Konfiguration
    und generiert eine Antwort.
    """
    provider = os.getenv("KI_PROVIDER", "kobold").lower()

    if provider == "gemini":
        return generate_reply_gemini(history, system_rules, user_message)
    elif provider == "kobold":
        return generate_reply_local(history, system_rules, user_message)
    else:
        print_ai_error(f"Unbekannter KI_PROVIDER '{provider}' in der Konfiguration.")
        return None