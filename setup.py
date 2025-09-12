#!/usr/bin/env python3
"""
VILUU Bot Setup Script
Automatische Installation und Konfiguration aller Abhängigkeiten.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description="", check_result=True):
    """Führt einen Befehl aus und gibt das Ergebnis zurück."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check_result)
        if result.returncode == 0:
            print(f"✅ {description} erfolgreich")
            return True
        else:
            print(f"❌ {description} fehlgeschlagen: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} fehlgeschlagen: {e}")
        return False


def check_python_version():
    """Überprüft die Python-Version."""
    print("🔍 Überprüfe Python-Version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor} ist kompatibel")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} ist nicht kompatibel. Benötigt Python 3.8+")
        return False


def install_requirements():
    """Installiert alle Python-Abhängigkeiten."""
    print("📦 Installiere Python-Abhängigkeiten...")
    
    # Update pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Aktualisiere pip")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        success = run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installiere Abhängigkeiten")
        if not success:
            print("⚠️ Fallback: Installiere Abhängigkeiten einzeln...")
            dependencies = [
                "playwright",
                "sqlite-utils", 
                "colorama",
                "requests",
                "python-dotenv",
                "google-generativeai"
            ]
            
            for dep in dependencies:
                run_command(f"{sys.executable} -m pip install {dep}", f"Installiere {dep}", check_result=False)
        return success
    else:
        print("❌ requirements.txt nicht gefunden")
        return False


def install_playwright_browsers():
    """Installiert Playwright-Browser."""
    print("🌐 Installiere Playwright-Browser...")
    success = run_command(f"{sys.executable} -m playwright install chromium", "Installiere Chromium-Browser", check_result=False)
    
    if not success:
        print("⚠️ Playwright-Browser-Installation fehlgeschlagen.")
        print("   Dies kann in bestimmten Umgebungen normal sein.")
        print("   Der Bot wird versuchen, Browser bei Bedarf automatisch zu installieren.")
        # Return True anyway as this might be environment-specific
        return True
    
    return success


def check_env_file():
    """Überprüft die .env-Datei."""
    print("⚙️ Überprüfe .env-Konfiguration...")
    if os.path.exists(".env"):
        print("✅ .env-Datei gefunden")
        
        # Check if we can import and validate
        try:
            from app.env_validator import validate_env_file, print_env_validation_results
            is_valid, errors = validate_env_file()
            print_env_validation_results(is_valid, errors)
            return is_valid
        except ImportError:
            print("⚠️ Kann Umgebungsvalidierung nicht durchführen (Module noch nicht installiert)")
            return True
    else:
        print("❌ .env-Datei nicht gefunden")
        print("📋 Erstelle eine .env-Datei mit folgenden Variablen:")
        print("   VILUU_USERNAME=dein_username")
        print("   VILUU_PASSWORD=dein_password")
        print("   KI_PROVIDER=gemini  # oder 'kobold'")
        print("   GEMINI_API_KEY=dein_api_key  # nur für Gemini")
        print("   KOBOLD_ENDPOINT=http://127.0.0.1:5001/api/v1/generate  # nur für Kobold")
        return False


def create_logs_directory():
    """Erstellt das Logs-Verzeichnis."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Logs-Verzeichnis erstellt")
    else:
        print("✅ Logs-Verzeichnis bereits vorhanden")
    return True


def main():
    """Hauptfunktion des Setup-Skripts."""
    print("=" * 60)
    print("          VILUU BOT - AUTOMATISCHES SETUP")
    print("=" * 60)
    print()
    
    success_count = 0
    total_checks = 6
    
    # 1. Python-Version prüfen
    if check_python_version():
        success_count += 1
    print()
    
    # 2. Abhängigkeiten installieren
    if install_requirements():
        success_count += 1
    print()
    
    # 3. Playwright-Browser installieren
    if install_playwright_browsers():
        success_count += 1
    print()
    
    # 4. Logs-Verzeichnis erstellen
    if create_logs_directory():
        success_count += 1
    print()
    
    # 5. .env-Datei prüfen
    if check_env_file():
        success_count += 1
    print()
    
    # 6. Finale Überprüfung
    print("🧪 Teste Bot-Import...")
    try:
        from app.bot_with_history import main as bot_main
        print("✅ Bot-Module können importiert werden")
        success_count += 1
    except Exception as e:
        print(f"❌ Bot-Import fehlgeschlagen: {e}")
    
    print()
    print("=" * 60)
    print(f"SETUP ABGESCHLOSSEN: {success_count}/{total_checks} Schritte erfolgreich")
    
    if success_count == total_checks:
        print("🎉 Alle Checks erfolgreich! Der Bot ist startklar.")
        print()
        print("🚀 NÄCHSTE SCHRITTE:")
        print("   1. Führe 'python run.py' aus, um den Bot zu starten")
        print("   2. Wähle deinen KI-Provider (Gemini oder Kobold)")
        print("   3. Folge den Anweisungen für Login und Chat-Navigation")
    else:
        print("⚠️ Einige Probleme müssen noch behoben werden.")
        print("   Überprüfe die Fehlermeldungen oben und führe das Setup erneut aus.")
    
    print("=" * 60)
    
    return success_count == total_checks


if __name__ == "__main__":
    main()