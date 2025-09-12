# VILUU Bot - Automatisierter Chat-Bot

Ein intelligenter Chat-Bot für die VILUU-Plattform mit Unterstützung für Google Gemini und lokale KI-Modelle.

## ✨ Features

- 🤖 **Dual-KI-Support**: Google Gemini (Online) oder lokales Kobold-Modell
- 🔄 **Automatische Wiederholung**: Retry-Logik bei Netzwerkfehlern
- 📊 **Umfassendes Logging**: Detaillierte Protokollierung aller Aktivitäten
- ⚙️ **Konfigurationsvalidierung**: Automatische Überprüfung der Umgebungseinstellungen
- 🛡️ **Robuste Fehlerbehandlung**: Graceful Degradation bei Problemen
- 🎯 **Follow-Up-Nachrichten**: Proaktive Nachfragen nach längerer Inaktivität

## 🚀 Schnellstart

### 1. Setup ausführen

**Windows:**
```batch
start_bot.bat
```

**Linux/Mac:**
```bash
python setup.py
```

### 2. Konfiguration

Erstelle eine `.env`-Datei im Hauptverzeichnis:

```env
# === KI-Konfiguration ===
KI_PROVIDER=gemini

# --- Login-Daten für VILUU ---
VILUU_USERNAME=dein_username
VILUU_PASSWORD=dein_passwort

# --- Google Gemini (nur wenn KI_PROVIDER=gemini) ---
GEMINI_API_KEY=dein_gemini_api_key

# --- Lokales Kobold-Modell (nur wenn KI_PROVIDER=kobold) ---
KOBOLD_ENDPOINT=http://127.0.0.1:5001/api/v1/generate
```

### 3. Bot starten

```bash
python run.py
```

## 📋 Systemanforderungen

- **Python 3.8+**
- **Internetverbindung** (für Gemini oder Browser-Download)
- **Chrome/Chromium Browser** (wird automatisch installiert)

### Python-Abhängigkeiten

Die folgenden Pakete werden automatisch installiert:

- `playwright` - Browser-Automation
- `google-generativeai` - Google Gemini API
- `sqlite-utils` - Datenbank-Management
- `colorama` - Farbige Konsolen-Ausgabe
- `requests` - HTTP-Anfragen
- `python-dotenv` - Umgebungsvariablen

## 🎮 Verwendung

### Hauptmenü

Nach dem Start erscheint das Hauptmenü:

```
=============================================
          VILUU BOT - STEUERZENTRALE         
=============================================

Status: ✅ Konfiguration OK (GEMINI)

[1] Google Gemini (Online, schnell und kreativ)
[2] Lokales Modell / Kobold (Offline, auf deinem PC)
[c] Konfiguration überprüfen
[q] Programm beenden
```

### Optionen

- **[1]** - Startet den Bot mit Google Gemini AI
- **[2]** - Startet den Bot mit lokalem Kobold-Modell
- **[c]** - Überprüft die Konfiguration
- **[q]** - Beendet das Programm

### Bot-Ablauf

1. **Login**: Automatisches Login bei VILUU
2. **Manuelle Navigation**: Du navigierst zum gewünschten Chat
3. **Überwachung**: Bot überwacht neue Nachrichten alle 15 Sekunden
4. **Antworten**: Automatische Generierung und Einfügung von Antworten
5. **Follow-Up**: Proaktive Nachrichten nach 4+ Stunden Inaktivität

## ⚙️ Konfiguration

### KI-Provider

#### Google Gemini
```env
KI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
```

- **Vorteile**: Schnell, kreativ, zuverlässig
- **API-Key**: Kostenlos bei [Google AI Studio](https://makersuite.google.com/)

#### Lokales Kobold-Modell
```env
KI_PROVIDER=kobold
KOBOLD_ENDPOINT=http://127.0.0.1:5001/api/v1/generate
```

- **Vorteile**: Vollständig offline, Datenschutz
- **Setup**: Benötigt lokalen KoboldCpp-Server

### Erweiterte Einstellungen

Die meisten Einstellungen sind bereits optimal konfiguriert:

- **Retry-Versuche**: 3x für Gemini, 2x für Kobold
- **Timeouts**: 180s für lokale Anfragen, 30s für Browser-Aktionen
- **Follow-Up-Intervall**: 4 Stunden
- **Chat-Überprüfung**: Alle 15 Sekunden

## 📊 Logging und Monitoring

### Log-Dateien

Alle Aktivitäten werden in `logs/viluu_bot.log` protokolliert:

```
2025-01-15 10:30:45 - VILUU_BOT - INFO - Bot-Start mit Google Gemini
2025-01-15 10:31:12 - VILUU_BOT - SUCCESS - ✅ KI-Anfrage erfolgreich - GEMINI (1.23s)
2025-01-15 10:31:15 - VILUU_BOT - INFO - Nachrichten verarbeitet: 5 (gespeichert)
```

### Fehlerbehandlung

Bei Fehlern:
- Automatische Wiederholung mit exponential backoff
- Detaillierte Fehlerprotokollierung
- Graceful Degradation (Bot läuft weiter)
- Maximale Anzahl aufeinanderfolgender Fehler: 5

## 🛠️ Troubleshooting

### Häufige Probleme

#### "Playwright-Browser nicht verfügbar"
```bash
python -m playwright install chromium
```

#### "Google Generative AI package missing"
```bash
pip install google-generativeai
```

#### "Login-Daten nicht gefunden"
- Überprüfe `.env`-Datei
- Führe `python run.py` aus und wähle `[c]` für Konfigurationsprüfung

#### "Lokales Modell nicht erreichbar"
- Starte KoboldCpp-Server
- Überprüfe `KOBOLD_ENDPOINT` in `.env`

### Logs überprüfen

```bash
# Aktuelle Logs anzeigen
tail -f logs/viluu_bot.log

# Fehler-Logs filtern
grep ERROR logs/viluu_bot.log
```

### Konfiguration testen

```bash
python -c "from app.env_validator import validate_env_file, print_env_validation_results; is_valid, errors = validate_env_file(); print_env_validation_results(is_valid, errors)"
```

## 🔒 Sicherheit

- **API-Keys**: Werden nur lokal in `.env` gespeichert
- **Login-Daten**: Verschlüsselte Übertragung über HTTPS
- **Browser**: Läuft in isolierter Playwright-Umgebung
- **Lokale Verarbeitung**: Chat-Verlauf wird nur lokal gespeichert

## 📈 Performance-Optimierung

### Für bessere Performance:

1. **SSD-Festplatte** für schnellere Datenbankzugriffe
2. **Stabile Internetverbindung** für Gemini API
3. **Ausreichend RAM** (min. 4GB) für Browser-Automation
4. **Lokale Modelle** für bessere Latenz (Kobold)

### Monitoring:

- Response-Zeiten werden geloggt
- Retry-Versuche werden gezählt
- Fehlerrate wird überwacht

## 🤝 Support

Bei Problemen:

1. **Setup ausführen**: `python setup.py`
2. **Konfiguration prüfen**: `python run.py` → `[c]`
3. **Logs überprüfen**: `logs/viluu_bot.log`
4. **Neustart**: Bot komplett neu starten

## 📄 Lizenz

Dieses Projekt ist für den persönlichen Gebrauch bestimmt. Bitte respektiere die Nutzungsbedingungen der verwendeten APIs und Plattformen.

---

**Viel Erfolg mit dem VILUU Bot! 🚀**