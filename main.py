import discord
import asyncio
import requests
import json
import os
import logging
from discord.ext import commands, tasks

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot-Konfiguration aus Umgebungsvariablen
TOKEN = os.environ.get('DISCORD_TOKEN')
GUILD_ID = int(os.environ.get('GUILD_ID', '0'))
ROLE_ID = int(os.environ.get('ROLE_ID', '0'))
SERVER_API = os.environ.get('SERVER_API')
API_KEY = os.environ.get('API_KEY')
WELCOME_CHANNEL_ID = int(os.environ.get('WELCOME_CHANNEL_ID', '0'))

# Bot-Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!azb ', intents=intents)

# Globale Variablen
server_online = False
last_check = None

@bot.event
async def on_ready():
    logger.info(f'🚀 Alpha Zentauri Base Bot ist online!')
    logger.info(f'📡 Bot-Name: {bot.user.name}#{bot.user.discriminator}')
    logger.info(f'🏠 Überwache Server: {GUILD_ID}')
    logger.info(f'🎭 Überwache Rolle: {ROLE_ID}')
    logger.info(f'🌐 FiveM Server: {SERVER_API}')
    
    # Status setzen
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Alpha Zentauri Base | !azb help"
        ),
        status=discord.Status.online
    )
    
    # Server-Check starten
    server_check.start()
    
    # Startup-Nachricht in Admin-Kanal
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            # Suche nach einem Admin-Kanal
            admin_channel = discord.utils.get(guild.channels, name='admin') or \
                           discord.utils.get(guild.channels, name='bot-logs') or \
                           guild.system_channel
            
            if admin_channel:
                embed = discord.Embed(
                    title="🤖 Bot gestartet",
                    description="Alpha Zentauri Base Discord Bot ist online!",
                    color=0x00ff00
                )
                embed.add_field(name="Version", value="1.0.0", inline=True)
                embed.add_field(name="Latenz", value=f"{round(bot.latency * 1000)}ms", inline=True)
                await admin_channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Fehler beim Senden der Startup-Nachricht: {e}")

@tasks.loop(minutes=5)
async def server_check():
    """Überprüft regelmäßig den FiveM-Server Status"""
    global server_online, last_check
    
    try:
        response = requests.get(f"{SERVER_API}/api/status", timeout=10)
        current_status = response.status_code == 200
        
        # Status-Änderung erkennen
        if server_online != current_status:
            server_online = current_status
            
            # Status-Update im Bot-Status
            if server_online:
                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name="Alpha Zentauri Base | Server Online"
                    ),
                    status=discord.Status.online
                )
                logger.info("✅ FiveM Server ist online")
            else:
                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name="Alpha Zentauri Base | Server Offline"
                    ),
                    status=discord.Status.idle
                )
                logger.warning("❌ FiveM Server ist offline")
        
        last_check = discord.utils.utcnow()
        
    except Exception as e:
        if server_online:  # Nur loggen wenn Server vorher online war
            logger.error(f"Server-Check Fehler: {e}")
            server_online = False
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="Alpha Zentauri Base | Server Check Failed"
                ),
                status=discord.Status.dnd
            )

@bot.event
async def on_member_update(before, after):
    # Nur auf dem konfigurierten Server reagieren
    if after.guild.id != GUILD_ID:
        return
        
    # Prüfen, ob die Rolle hinzugefügt wurde
    had_role = discord.utils.get(before.roles, id=ROLE_ID)
    has_role = discord.utils.get(after.roles, id=ROLE_ID)
    
    if not had_role and has_role:
        logger.info(f'✅ Rolle hinzugefügt für {after.name}#{after.discriminator} (ID: {after.id})')
        
        try:
            # FiveM-Server API aufrufen
            response = requests.post(
                f"{SERVER_API}/api/create-account",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                json={
                    "discord_id": str(after.id),
                    "discord_username": f"{after.name}#{after.discriminator}"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Account für {after.name} erfolgreich erstellt")
                
                # Kurz warten, damit der Server die Daten verarbeiten kann
                await asyncio.sleep(3)
                
                # Willkommensnachricht per DM
                embed = discord.Embed(
                    title="🚀 Willkommen bei Alpha Zentauri Base!",
                    description="Dein Account wurde erfolgreich erstellt!",
                    color=0x9932cc
                )
                
                embed.add_field(
                    name="📋 So verbindest du dich:",
                    value=f"1. **Starte FiveM**\n2. **Drücke F8** und gib ein:\n```connect {SERVER_API.replace('http://', '').replace(':30120', '')}```\n3. **Gib deine Zugangsdaten ein** (wurden automatisch erstellt)\n4. **Erstelle deinen Charakter** und starte dein Roleplay-Abenteuer!",
                    inline=False
                )
                
                embed.add_field(
                    name="🔐 Wichtige Sicherheitshinweise:",
                    value="• Deine Zugangsdaten sind **einzigartig** und **persönlich**\n• **Teile sie niemals** mit anderen Personen\n• Bei Problemen wende dich an unsere **Admins**\n• **Speichere** deine Daten sicher ab",
                    inline=False
                )
                
                embed.add_field(
                    name="📖 Bevor du startest:",
                    value="• Lies unsere **Server-Regeln** im Discord\n• Schau dir die **Roleplay-Guidelines** an\n• Bei Fragen nutze den **Support-Bereich**\n• Hab Spaß und respektiere andere Spieler!",
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Server-Information:",
                    value=f"**Server:** Alpha Zentauri Base\n**Typ:** GTA V Roleplay\n**Framework:** ESX\n**Sprache:** Deutsch",
                    inline=False
                )
                
                embed.set_footer(text="Alpha Zentauri Base - Dein Premium GTA Roleplay Server")
                embed.set_thumbnail(url="https://i.imgur.com/placeholder.png")  # Ersetze mit deinem Server-Logo
                
                dm_sent = False
                try:
                    await after.send(embed=embed)
                    dm_sent = True
                    logger.info(f"📨 Willkommensnachricht per DM an {after.name} gesendet")
                except discord.Forbidden:
                    logger.warning(f"❌ Kann keine DM an {after.name} senden (DMs deaktiviert)")
                except Exception as e:
                    logger.error(f"❌ Fehler beim Senden der DM an {after.name}: {e}")
                
                # Falls DM nicht funktioniert, Nachricht im Welcome-Channel
                if not dm_sent and WELCOME_CHANNEL_ID:
                    try:
                        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
                        if welcome_channel:
                            public_embed = discord.Embed(
                                title="🎉 Neuer Spieler!",
                                description=f"Willkommen {after.mention} bei Alpha Zentauri Base!",
                                color=0x9932cc
                            )
                            public_embed.add_field(
                                name="📨 Wichtiger Hinweis:",
                                value="Deine Zugangsdaten wurden per **Direktnachricht** gesendet.\nFalls du keine Nachricht erhalten hast, **aktiviere bitte DMs** von Servermitgliedern in deinen Discord-Einstellungen.",
                                inline=False
                            )
                            public_embed.set_footer(text="Alpha Zentauri Base")
                            
                            await welcome_channel.send(embed=public_embed)
                            logger.info(f"📨 Öffentliche Willkommensnachricht für {after.name} gesendet")
                    except Exception as e:
                        logger.error(f"Fehler beim Senden der öffentlichen Nachricht: {e}")
                        
            else:
                logger.error(f"❌ Server-Fehler beim Erstellen des Accounts: {response.status_code} - {response.text}")
                
                # Fehler-Nachricht an Admins
                try:
                    guild = bot.get_guild(GUILD_ID)
                    admin_channel = discord.utils.get(guild.channels, name='admin') or \
                                   discord.utils.get(guild.channels, name='bot-logs')
                    
                    if admin_channel:
                        error_embed = discord.Embed(
                            title="❌ Account-Erstellung fehlgeschlagen",
                            description=f"Fehler beim Erstellen des Accounts für {after.mention}",
                            color=0xff0000
                        )
                        error_embed.add_field(name="Benutzer", value=f"{after.name}#{after.discriminator}", inline=True)
                        error_embed.add_field(name="Discord ID", value=str(after.id), inline=True)
                        error_embed.add_field(name="Fehlercode", value=str(response.status_code), inline=True)
                        error_embed.add_field(name="Fehlermeldung", value=response.text[:1000], inline=False)
                        
                        await admin_channel.send(embed=error_embed)
                except Exception as e:
                    logger.error(f"Fehler beim Senden der Admin-Benachrichtigung: {e}")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout beim Verbinden zum FiveM-Server für {after.name}")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Verbindungsfehler zum FiveM-Server für {after.name}")
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler bei der Account-Erstellung für {after.name}: {e}")

# Admin-Befehle
@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def server_status(ctx):
    """Zeigt den detaillierten Status des FiveM-Servers"""
    try:
        response = requests.get(f"{SERVER_API}/api/status", timeout=10)
        
        embed = discord.Embed(
            title="🖥️ Server-Status",
            color=0x00ff00 if response.status_code == 200 else 0xff0000
        )
        
        if response.status_code == 200:
            data = response.json()
            embed.description = "✅ FiveM-Server ist **online** und erreichbar"
            embed.add_field(name="Status", value=data.get('status', 'Unknown'), inline=True)
            embed.add_field(name="Letzter Check", value=f"<t:{int(last_check.timestamp())}:R>" if last_check else "Nie", inline=True)
            embed.add_field(name="Response Time", value=f"{response.elapsed.total_seconds():.2f}s", inline=True)
        else:
            embed.description = f"❌ Server antwortet nicht (HTTP {response.status_code})"
            
        embed.add_field(name="Server API", value=SERVER_API, inline=False)
        embed.set_footer(text=f"Angefragt von {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
    except requests.exceptions.Timeout:
        embed = discord.Embed(
            title="⏰ Timeout",
            description="Server antwortet nicht innerhalb von 10 Sekunden",
            color=0xffaa00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ Verbindungsfehler",
            description=f"Fehler beim Verbinden: {str(e)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='create')
@commands.has_permissions(administrator=True)
async def create_account_manual(ctx, member: discord.Member):
    """Erstellt manuell einen Account für einen Benutzer"""
    try:
        response = requests.post(
            f"{SERVER_API}/api/create-account",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "discord_id": str(member.id),
                "discord_username": f"{member.name}#{member.discriminator}"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            embed = discord.Embed(
                title="✅ Account erstellt",
                description=f"Account für {member.mention} wurde **erfolgreich erstellt**!",
                color=0x00ff00
            )
            embed.add_field(name="Benutzer", value=f"{member.name}#{member.discriminator}", inline=True)
            embed.add_field(name="Discord ID", value=str(member.id), inline=True)
            embed.add_field(name="Erstellt von", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"✅ Manueller Account für {member.name} von {ctx.author.name} erstellt")
        else:
            embed = discord.Embed(
                title="❌ Fehler beim Erstellen",
                description=f"**HTTP {response.status_code}**\n```{response.text[:500]}```",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            
    except Exception as e:
        embed = discord.Embed(
            title="❌ Unerwarteter Fehler",
            description=f"```{str(e)[:500]}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='info')
async def bot_info(ctx):
    """Zeigt Bot-Informationen und Statistiken"""
    embed = discord.Embed(
        title="🤖 Alpha Zentauri Base Bot",
        description="Discord-Bot für das FiveM Login-System",
        color=0x9932cc
    )
    
    embed.add_field(name="📊 Statistiken", value=f"**Latenz:** {round(bot.latency * 1000)}ms\n**Server:** {len(bot.guilds)}\n**Benutzer:** {len(bot.users)}", inline=True)
    embed.add_field(name="🔧 Version", value="**Bot:** 1.0.0\n**Discord.py:** 2.3.2\n**Python:** 3.11", inline=True)
    embed.add_field(name="🌐 Status", value=f"**FiveM:** {'🟢 Online' if server_online else '🔴 Offline'}\n**Uptime:** <t:{int(bot.user.created_at.timestamp())}:R>", inline=True)
    
    embed.add_field(name="📋 Verfügbare Befehle", value="**!azb status** - Server-Status\n**!azb create @user** - Account erstellen\n**!azb info** - Bot-Informationen", inline=False)
    
    embed.set_footer(text="Alpha Zentauri Base - Entwickelt für das beste Roleplay-Erlebnis")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Zeigt alle verfügbaren Befehle"""
    embed = discord.Embed(
        title="📚 Alpha Zentauri Base Bot - Hilfe",
        description="Hier sind alle verfügbaren Befehle:",
        color=0x9932cc
    )
    
    embed.add_field(
        name="👥 Allgemeine Befehle",
        value="**!azb info** - Bot-Informationen\n**!azb help** - Diese Hilfe anzeigen",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Admin-Befehle",
        value="**!azb status** - FiveM-Server Status\n**!azb create @user** - Manuell Account erstellen",
        inline=False
    )
    
    embed.add_field(
        name="🔄 Automatische Funktionen",
        value="• **Automatische Account-Erstellung** bei Rollenzuweisung\n• **Willkommensnachrichten** per DM\n• **Server-Überwachung** alle 5 Minuten",
        inline=False
    )
    
    embed.set_footer(text="Alpha Zentauri Base - Bei Fragen wende dich an die Admins")
    
    await ctx.send(embed=embed)

# Fehlerbehandlung
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Keine Berechtigung",
            description="Du hast nicht die erforderlichen **Administrator-Berechtigungen** für diesen Befehl.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        # Ignoriere unbekannte Befehle
        pass
    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            title="❌ Benutzer nicht gefunden",
            description="Der angegebene Benutzer konnte nicht gefunden werden.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    else:
        logger.error(f"Unerwarteter Befehlsfehler: {error}")
        embed = discord.Embed(
            title="❌ Unerwarteter Fehler",
            description="Ein unerwarteter Fehler ist aufgetreten. Bitte kontaktiere einen Administrator.",
            color=0xff0000
        )
        await ctx.send(embed=embed)

# Bot starten
if __name__ == "__main__":
    # Überprüfe erforderliche Umgebungsvariablen
    required_vars = ['DISCORD_TOKEN', 'GUILD_ID', 'ROLE_ID', 'SERVER_API', 'API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ Fehlende Umgebungsvariablen: {', '.join(missing_vars)}")
        exit(1)
    
    logger.info("🚀 Starte Alpha Zentauri Base Discord Bot...")
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Ungültiger Discord-Token!")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim Starten: {e}")
        exit(1)
