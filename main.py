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

# Bot-Konfiguration aus Umgebungsvariablen (OHNE dotenv)
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

# Bot erstellen OHNE eingebauten help-Command
bot = commands.Bot(command_prefix='!azb ', intents=intents, help_command=None)

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
            name="Alpha Zentauri Base | !azb info"
        ),
        status=discord.Status.online
    )
    
    # Server-Check starten
    server_check.start()

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
        if server_online:
            logger.error(f"Server-Check Fehler: {e}")
            server_online = False

@bot.event
async def on_member_update(before, after):
    # Nur auf dem konfigurierten Server reagieren
    if after.guild.id != GUILD_ID:
        return
        
    # Prüfen, ob die Rolle hinzugefügt wurde
    had_role = discord.utils.get(before.roles, id=ROLE_ID)
    has_role = discord.utils.get(after.roles, id=ROLE_ID)
    
    if not had_role and has_role:
        logger.info(f'✅ Rolle hinzugefügt für {after.name}#{after.discriminator}')
        
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
                
                # Kurz warten
                await asyncio.sleep(3)
                
                # Willkommensnachricht per DM
                embed = discord.Embed(
                    title="🚀 Willkommen bei Alpha Zentauri Base!",
                    description="Dein Account wurde erfolgreich erstellt!",
                    color=0x9932cc
                )
                
                embed.add_field(
                    name="📋 So verbindest du dich:",
                    value=f"1. **Starte FiveM**\n2. **Drücke F8** und gib ein:\n```connect {SERVER_API.replace('http://', '').replace(':30120', '')}```\n3. **Gib deine Zugangsdaten ein**\n4. **Erstelle deinen Charakter**\n\n**Discord:** https://discord.gg/pvVDVVK9jc",
                    inline=False
                )
                
                embed.set_footer(text="Alpha Zentauri Base - Dein Premium GTA Roleplay Server")
                
                try:
                    await after.send(embed=embed)
                    logger.info(f"📨 Willkommensnachricht an {after.name} gesendet")
                except discord.Forbidden:
                    logger.warning(f"❌ Kann keine DM an {after.name} senden")
                        
            else:
                logger.error(f"❌ Server-Fehler: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Account-Erstellung: {e}")

# Commands
@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def server_status(ctx):
    """Zeigt den Status des FiveM-Servers"""
    try:
        response = requests.get(f"{SERVER_API}/api/status", timeout=10)
        
        embed = discord.Embed(
            title="🖥️ Server-Status",
            color=0x00ff00 if response.status_code == 200 else 0xff0000
        )
        
        if response.status_code == 200:
            embed.description = "✅ FiveM-Server ist **online**"
        else:
            embed.description = f"❌ Server antwortet nicht (HTTP {response.status_code})"
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ Verbindungsfehler",
            description=f"Fehler: {str(e)}",
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
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Fehler",
                description=f"HTTP {response.status_code}: {response.text[:500]}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            
    except Exception as e:
        embed = discord.Embed(
            title="❌ Fehler",
            description=f"```{str(e)[:500]}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='info')
async def bot_info(ctx):
    """Zeigt Bot-Informationen"""
    embed = discord.Embed(
        title="🤖 Alpha Zentauri Base Bot",
        description="Discord-Bot für das FiveM Login-System",
        color=0x9932cc
    )
    
    embed.add_field(
        name="📊 Status", 
        value=f"**Latenz:** {round(bot.latency * 1000)}ms\n**Server:** {'🟢 Online' if server_online else '🔴 Offline'}", 
        inline=True
    )
    embed.add_field(
        name="📋 Commands", 
        value="**!azb status** - Server prüfen\n**!azb create @user** - Account erstellen\n**!azb info** - Bot-Info", 
        inline=True
    )
    
    embed.add_field(
        name="🔗 Links",
        value="**Discord:** https://discord.gg/pvVDVVK9jc\n**Server:** Alpha Zentauri Base RP",
        inline=False
    )
    
    embed.set_footer(text="Alpha Zentauri Base - Entwickelt für das beste Roleplay")
    
    await ctx.send(embed=embed)

# Fehlerbehandlung
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Keine Berechtigung",
            description="Du brauchst **Administrator-Rechte** für diesen Befehl.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignoriere unbekannte Befehle
    else:
        logger.error(f"Command-Fehler: {error}")

# Bot starten
if __name__ == "__main__":
    # Überprüfe Umgebungsvariablen
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
        logger.error(f"❌ Kritischer Fehler: {e}")
        exit(1)
