import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()

# RATE LIMIT PROTECTION
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Configurar logging SIN flood
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logging.getLogger('discord.gateway').setLevel(logging.CRITICAL)

bot = commands.Bot(
    command_prefix='!', 
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# Configuración
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except:
    config = {"prefix": "!", "default_volume": 0.5}

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} conectado en {len(bot.guilds)} servidores')
    print(f'📱 ID: {bot.user.id}')
    
    try:
        await bot.load_extension('cogs.music', package=None)
        print('✅ Módulo música cargado')
    except Exception as e:
        print(f'❌ Error cargando música: {e}')

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'Error en {event}')

# TOKEN CHECK
token = os.getenv('DISCORD_TOKEN')
if not token:
    print('❌ DISCORD_TOKEN no encontrado en variables de entorno')
    exit(1)

if __name__ == '__main__':
    try:
        bot.run(token, log_handler=None)
    except discord.errors.LoginFailure:
        print('❌ TOKEN INVÁLIDO. Ve a Discord Developer Portal → Regenera token')
    except Exception as e:
        print(f'❌ Error crítico: {e}')
