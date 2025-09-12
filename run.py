# run.py
"""
VILUU Bot - Hauptstartskript
Bietet ein benutzerfreundliches Menü zur Auswahl des KI-Providers.
"""
import os
import sys
from app.bot_with_history import main
from app.env_validator import validate_env_file, print_env_validation_results, get_env_status_summary
from app.logger import logger, log_startup, log_shutdown


def clear_screen():
    """Plattformunabhängige Bildschirm-Löschung."""
    os.system('cls' if os.name == 'nt' else 'clear')


def check_and_install_playwright():
    """Überprüft und installiert Playwright-Browser falls nötig."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Teste ob Chromium verfügbar ist
            browser = p.chromium.launch(headless=True)
            browser.close()
            logger.success("Playwright-Browser sind verfügbar")
            return True
    except Exception as e:
        logger.warning("Playwright-Browser nicht verfügbar, versuche Installation...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.success("Playwright-Browser erfolgreich installiert")
                return True
            else:
                logger.error(f"Playwright-Installation fehlgeschlagen: {result.stderr}")
                return False
        except Exception as install_error:
            logger.error("Fehler bei Playwright-Installation", install_error)
            return False


def show_main_menu():
    """Zeigt das Hauptmenü an."""
    clear_screen()
    
    print("=============================================")
    print("          VILUU BOT - STEUERZENTRALE         ")
    print("=============================================")
    
    # Zeige Konfigurationsstatus
    env_status = get_env_status_summary()
    print(f"\nStatus: {env_status}")
    
    print("\nWelche KI möchtest du für diesen Lauf nutzen?")
    print("\n[1] Google Gemini (Online, schnell und kreativ)")
    print("[2] Lokales Modell / Kobold (Offline, auf deinem PC)")
    print("\n[c] Konfiguration überprüfen")
    print("[q] Programm beenden")
    print("\n=============================================")


def get_user_choice():
    """Holt und validiert die Benutzereingabe."""
    while True:
        try:
            choice = input("Deine Wahl (1, 2, c oder q): ").strip().lower()
            if choice in ['1', '2', 'c', 'q']:
                return choice
            else:
                print("❌ Ungültige Eingabe. Bitte wähle 1, 2, c oder q.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nProgramm wird beendet...")
            return 'q'


def handle_config_check():
    """Führt eine Konfigurationsprüfung durch."""
    clear_screen()
    print("🔧 KONFIGURATIONSPRÜFUNG")
    print("=" * 50)
    
    is_valid, errors = validate_env_file()
    print_env_validation_results(is_valid, errors)
    
    print("\n" + "=" * 50)
    input("Drücke ENTER um zum Hauptmenü zurückzukehren...")


def start_bot_with_provider(provider: str, provider_name: str):
    """Startet den Bot mit dem angegebenen Provider."""
    
    # Validate environment first
    is_valid, errors = validate_env_file()
    if not is_valid:
        clear_screen()
        print(f"❌ Kann {provider_name} nicht starten - Konfigurationsfehler:")
        print_env_validation_results(is_valid, errors)
        input("\nDrücke ENTER um zum Hauptmenü zurückzukehren...")
        return
    
    # Check Playwright installation
    if not check_and_install_playwright():
        clear_screen()
        print("❌ Playwright-Browser konnten nicht installiert werden.")
        print("Bitte installiere sie manuell mit: playwright install chromium")
        input("\nDrücke ENTER um zum Hauptmenü zurückzukehren...")
        return
    
    clear_screen()
    print(f"🚀 Starte VILUU Bot mit {provider_name}...")
    
    if provider == "kobold":
        print("\n⚠️  WICHTIG für Kobold:")
        print("   Stelle sicher, dass dein lokaler Server läuft!")
        print("   (z.B. KoboldCpp auf http://127.0.0.1:5001)")
        
    print("\n" + "=" * 50)
    logger.info(f"Bot-Start mit {provider_name}")
    
    try:
        main(ki_provider=provider)
    except KeyboardInterrupt:
        logger.info("Bot durch Benutzer beendet (Ctrl+C)")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Bot-Start", e)
        print(f"\n❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        input("Drücke ENTER um fortzufahren...")


def start():
    """Hauptfunktion - startet das Menüsystem."""
    log_startup()
    
    try:
        while True:
            show_main_menu()
            choice = get_user_choice()
            
            if choice == '1':
                start_bot_with_provider("gemini", "Google Gemini")
                break  # Bot beendet, zurück zum System
                
            elif choice == '2':
                start_bot_with_provider("kobold", "Lokales Kobold-Modell")
                break  # Bot beendet, zurück zum System
                
            elif choice == 'c':
                handle_config_check()
                continue  # Zurück zum Hauptmenü
                
            elif choice == 'q':
                clear_screen()
                print("👋 Auf Wiedersehen! VILUU Bot wird beendet.")
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 Programm durch Benutzer beendet.")
    except Exception as e:
        logger.error("Unerwarteter Fehler im Hauptmenü", e)
        print(f"\n❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        log_shutdown()


if __name__ == "__main__":
    start()