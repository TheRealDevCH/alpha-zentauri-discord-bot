# Alpha Zentauri Base Discord Bot

Discord-Bot für das automatische FiveM Login-System.

## Features

- 🔄 **Automatische Account-Erstellung** bei Discord-Rollenzuweisung
- 📨 **Willkommensnachrichten** per Direktnachricht
- 🖥️ **Server-Überwachung** mit Status-Updates
- 🛠️ **Admin-Befehle** für manuelle Account-Verwaltung
- 📊 **Detaillierte Logs** und Fehlerbehandlung

## Befehle

### Allgemeine Befehle
- `!azb info` - Bot-Informationen anzeigen
- `!azb help` - Hilfe anzeigen

### Admin-Befehle
- `!azb status` - FiveM-Server Status prüfen
- `!azb create @user` - Manuell Account für Benutzer erstellen

## Umgebungsvariablen

\`\`\`
DISCORD_TOKEN=dein_discord_bot_token
GUILD_ID=deine_discord_server_id
ROLE_ID=deine_rollen_id
SERVER_API=http://deine-server-ip:30120
API_KEY=dein_geheimer_api_key
WELCOME_CHANNEL_ID=kanal_id_für_willkommensnachrichten
\`\`\`

## Installation

1. Repository klonen
2. Umgebungsvariablen setzen
3. `pip install -r requirements.txt`
4. `python main.py`

## Support

Bei Fragen oder Problemen wende dich an die Alpha Zentauri Base Admins.
