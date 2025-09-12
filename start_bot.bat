@echo off
REM ===============================================
REM       VILUU BOT - Windows Startskript
REM ===============================================

ECHO.
ECHO ===============================================
ECHO          VILUU BOT wird gestartet...
ECHO ===============================================
ECHO.

REM Überprüfe ob Python verfügbar ist
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ❌ Python ist nicht installiert oder nicht im PATH.
    ECHO    Bitte installiere Python 3.8+ von https://python.org
    PAUSE
    EXIT /B 1
)

REM Überprüfe ob das Skript im richtigen Verzeichnis ausgeführt wird
IF NOT EXIST "run.py" (
    ECHO ❌ run.py nicht gefunden. 
    ECHO    Führe dieses Skript im VILUU-Bot Verzeichnis aus.
    PAUSE
    EXIT /B 1
)

REM Überprüfe ob .env-Datei existiert
IF NOT EXIST ".env" (
    ECHO ⚠️  .env-Datei nicht gefunden.
    ECHO    Führe zuerst das Setup aus: python setup.py
    PAUSE
    EXIT /B 1
)

REM Versuche virtuelle Umgebung zu aktivieren (optional)
IF EXIST ".venv\Scripts\activate.bat" (
    ECHO 🔧 Aktiviere virtuelle Umgebung...
    CALL .\.venv\Scripts\activate.bat
)

REM Führe automatisches Setup aus (installiert fehlende Abhängigkeiten)
ECHO 🔧 Führe automatisches Setup aus...
python setup.py
IF ERRORLEVEL 1 (
    ECHO.
    ECHO ❌ Setup fehlgeschlagen. Überprüfe die Fehlermeldungen.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO 🚀 Starte VILUU Bot...
ECHO.

REM Starte das Hauptprogramm
python run.py

ECHO.
ECHO ===============================================
ECHO          Bot-Sitzung beendet
ECHO ===============================================
pause