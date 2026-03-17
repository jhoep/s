import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import aiohttp

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Cargar configuración
with open('config.json', 'r') as f:
    config = json.load(f)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} conectado en {len(bot.guilds)} servidores')
    await bot.load_extension('cogs.music')

bot.run(os.getenv('DISCORD_TOKEN'))