# Automation Verbesserungen

## Übersicht

Die Bot-Automatisierung wurde erheblich verbessert, um lange Pausen zu reduzieren und bessere Debug-Möglichkeiten zu bieten.

## Neue Konfigurationsoptionen

Alle Einstellungen können über Umgebungsvariablen in der `.env` Datei konfiguriert werden:

### Timing und Automatisierung
```bash
# Polling-Intervall in Sekunden (Standard: 15)
BOT_POLLING_INTERVAL=15

# Retry-Verzögerung in Millisekunden (Standard: 700)
BOT_RETRY_DELAY=700

# Follow-Up Trigger-Zeit in Stunden (Standard: 4)
BOT_FOLLOW_UP_HOURS=4

# Seiten-Ladezeit-Timeout in Millisekunden (Standard: 20000)
BOT_PAGE_LOAD_TIMEOUT=20000
```

### Debug und Automatisierungsgrad
```bash
# Debug-Level: 0=minimal, 1=normal, 2=verbose (Standard: 1)
BOT_DEBUG_LEVEL=1

# Manuelle Schritte automatisch überspringen (Standard: false)
BOT_AUTO_SKIP_MANUAL=false

# Automatisch fortfahren ohne Benutzer-Eingaben (Standard: false)
BOT_AUTO_CONTINUE=false
```

## Verbesserungen

### 1. Konfigurierbare Pausen
- **Vorher**: Feste 15-Sekunden-Pausen
- **Nachher**: Konfigurierbar via `BOT_POLLING_INTERVAL`
- **Vorteil**: Schnellere Reaktionszeiten oder weniger Ressourcenverbrauch je nach Bedarf

### 2. Debug-Level System
- **Level 0**: Nur kritische Meldungen
- **Level 1**: Normale Status-Updates (Standard)
- **Level 2**: Detaillierte Debug-Informationen und Stack-Traces

### 3. Vollautomatisierung
- `BOT_AUTO_SKIP_MANUAL=true`: Überspringt manuelle Navigation
- `BOT_AUTO_CONTINUE=true`: Keine "ENTER drücken" Prompts
- **Nutzen**: Für Produktionseinsatz ohne manuellen Eingriff

### 4. Verbesserte Fehlerbehandlung
- Detaillierte Fehlermeldungen mit Typ-Informationen
- Konfigurierbare Stack-Trace-Anzeige
- Bessere Timeout- und Retry-Nachrichten

### 5. Status-Indikatoren
- Anzeige aktueller Polling-Intervalle
- Follow-Up-Timing-Informationen
- Nachrichten-Zähler und Entscheidungslogik

## Beispiel-Konfigurationen

### Schneller Debug-Modus
```bash
BOT_POLLING_INTERVAL=5
BOT_DEBUG_LEVEL=2
BOT_RETRY_DELAY=300
```

### Produktions-Modus
```bash
BOT_POLLING_INTERVAL=30
BOT_DEBUG_LEVEL=0
BOT_AUTO_SKIP_MANUAL=true
BOT_AUTO_CONTINUE=true
```

### Entwicklungs-Modus
```bash
BOT_POLLING_INTERVAL=10
BOT_DEBUG_LEVEL=2
BOT_FOLLOW_UP_HOURS=1
```

## Verwendung

Die Konfiguration wird automatisch beim Start geladen. Beispiel:

```bash
# In .env Datei setzen
echo "BOT_DEBUG_LEVEL=2" >> .env
echo "BOT_POLLING_INTERVAL=10" >> .env

# Bot starten
python run.py
```

## Log-Ausgaben

Mit den neuen Debug-Leveln erhalten Sie:

- **🔧 DEBUG**: Technische Details und Ablaufverfolgung
- **ℹ️ STATUS**: Wichtige Statusänderungen
- **📝 VERBOSE**: Detaillierte Informationen bei Level 2

Diese Verbesserungen reduzieren unnötige Wartezeiten und bieten bessere Kontrolle über die Automatisierung.