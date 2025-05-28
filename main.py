import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID'))
SERVER_API = os.getenv('SERVER_API')
VERIFIED_ROLE_ID = int(os.getenv('VERIFIED_ROLE_ID'))
UNVERIFIED_ROLE_ID = int(os.getenv('UNVERIFIED_ROLE_ID'))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    rules_channel = bot.get_channel(RULES_CHANNEL_ID)
    await channel.send(f"Willkommen {member.mention} auf unserem Server!\nBitte lies dir die Regeln in {rules_channel.mention} durch und verifiziere dich, um Zugriff auf alle Kanäle zu erhalten.")
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    await member.add_roles(unverified_role)

@bot.event
async def on_member_update(before, after):
    if UNVERIFIED_ROLE_ID in [role.id for role in before.roles] and VERIFIED_ROLE_ID in [role.id for role in after.roles]:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        value=f"1. **Starte FiveM**\n2. **Drücke F8** und gib ein:\n\`\`\`connect localhost\`\`\`\n3. **Gib deine Zugangsdaten ein**\n4. **Erstelle deinen Charakter**\n\n**Discord:** https://discord.gg/pvVDVVK9jc",
        embed = discord.Embed(title="Wie du auf den Server kommst:", description=value, color=0x00ff00)
        await channel.send(f"Viel Spaß auf dem Server, {after.mention}!", embed=embed)

bot.run(TOKEN)
