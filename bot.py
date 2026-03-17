import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import asyncio
import logging

# Configurar logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

load_dotenv()

# PYTHON 3.14 FIX: Evitar audioop
os.environ['PYNACL_USE_SYSTEM_LIB'] = '1'

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuración
with open('config.json', 'r') as f:
    config = json.load(f)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} conectado!')
    try:
        await bot.load_extension('cogs.music')
        print('✅ Módulo música cargado')
    except Exception as e:
        print(f'❌ Error cargando música: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f'Error: {error}')

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
