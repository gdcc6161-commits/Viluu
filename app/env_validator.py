"""
Environment validation module for VILUU bot.
Ensures all required environment variables are properly configured.
"""
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv


def validate_env_file() -> Tuple[bool, List[str]]:
    """
    Validates the .env file and required environment variables.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    load_dotenv()
    
    errors = []
    
    # Check if .env file exists
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_file_path):
        errors.append("❌ .env Datei nicht gefunden. Bitte erstelle eine .env Datei im Hauptverzeichnis.")
        return False, errors
    
    # Required variables
    required_vars = {
        'VILUU_USERNAME': 'Benutzername für VILUU Login',
        'VILUU_PASSWORD': 'Passwort für VILUU Login',
        'KI_PROVIDER': 'KI-Anbieter (gemini oder kobold)'
    }
    
    # Optional variables (checked based on KI_PROVIDER)
    ki_provider = os.getenv('KI_PROVIDER', '').lower()
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.strip() == '':
            errors.append(f"❌ {var} fehlt oder ist leer. ({description})")
    
    # Provider-specific validation
    if ki_provider == 'gemini':
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key or gemini_api_key.strip() == '':
            errors.append("❌ GEMINI_API_KEY fehlt oder ist leer. Benötigt für Google Gemini.")
        elif len(gemini_api_key.strip()) < 20:
            errors.append("⚠️ GEMINI_API_KEY scheint zu kurz zu sein. Überprüfe den API-Key.")
            
    elif ki_provider == 'kobold':
        kobold_endpoint = os.getenv('KOBOLD_ENDPOINT')
        if not kobold_endpoint or kobold_endpoint.strip() == '':
            errors.append("❌ KOBOLD_ENDPOINT fehlt oder ist leer. Benötigt für lokales Kobold-Modell.")
        elif not kobold_endpoint.startswith(('http://', 'https://')):
            errors.append("⚠️ KOBOLD_ENDPOINT sollte mit http:// oder https:// beginnen.")
    
    elif ki_provider not in ['gemini', 'kobold']:
        errors.append(f"❌ KI_PROVIDER '{ki_provider}' ist ungültig. Verwende 'gemini' oder 'kobold'.")
    
    return len(errors) == 0, errors


def print_env_validation_results(is_valid: bool, errors: List[str]) -> bool:
    """
    Prints validation results in a user-friendly format.
    
    Returns:
        bool: True if valid, False if errors exist
    """
    if is_valid:
        print("✅ Umgebungskonfiguration ist vollständig und korrekt!")
        return True
    else:
        print("\n🔧 KONFIGURATIONSPROBLEME GEFUNDEN:")
        print("=" * 50)
        for error in errors:
            print(f"  {error}")
        
        print("\n📋 HILFE:")
        print("  - Überprüfe deine .env Datei im Hauptverzeichnis")
        print("  - Stelle sicher, dass alle erforderlichen Variablen gesetzt sind")
        print("  - Für Gemini: Erstelle einen API-Key unter https://makersuite.google.com/")
        print("  - Für Kobold: Starte deinen lokalen Server (z.B. KoboldCpp)")
        print("=" * 50)
        return False


def get_env_status_summary() -> str:
    """
    Returns a brief status summary of the environment configuration.
    """
    is_valid, errors = validate_env_file()
    
    if is_valid:
        ki_provider = os.getenv('KI_PROVIDER', 'unbekannt').upper()
        return f"✅ Konfiguration OK ({ki_provider})"
    else:
        return f"❌ {len(errors)} Konfigurationsfehler"