@echo off
ECHO Starte den VILUU BOT...
ECHO.

REM Aktiviere die virtuelle Umgebung
CALL .\.venv\Scripts\activate

REM Starte das Hauptprogramm
python run.py

ECHO.
ECHO Bot-Sitzung beendet.
pause