import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import aiohttp
import json
import os
from typing import Optional

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.cookies = None
        self.load_cookies()
        
    def load_cookies(self):
        """Carga cookies para YouTube Premium/Mejor calidad"""
        cookie_file = 'youtube_cookies.txt'
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                self.cookies = f.read()
            print("✅ Cookies cargadas para mejor calidad")
    
    def get_yt_dlp_options(self):
        """Configuración optimizada de yt-dlp con cookies"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'cookies': self.cookies,
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        return ydl_opts
    
    async def search_youtube(self, query: str):
        """Búsqueda optimizada de YouTube"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookies': self.cookies,
            'default_search': 'ytsearch5:',
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await asyncio.to_thread(ydl.extract_info, query, download=False)
                return info['entries'][:5] if 'entries' in info else [info]
            except Exception:
                return []
    
    async def play_next(self, ctx):
        """Reproduce la siguiente canción en la cola"""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            await ctx.send("✅ Cola vacía. Usa `!play` para agregar canciones")
            return
        
        queue = self.queues[ctx.guild.id]
        song = queue.popleft()
        
        try:
            ydl_opts = self.get_yt_dlp_options()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(song['url'], download=False))
                url2 = info['url']
                title = info.get('title', 'Desconocido')
                
            voice_client = ctx.guild.voice_client
            source = discord.FFmpegPCMAudio(url2, **{
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            })
            
            voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
            )
            
            embed = discord.Embed(
                title="🎵 Reproduciendo ahora",
                description=f"**[{title}]({song['url']})**",
                color=0x00ff00
            )
            embed.add_field(name="📊 Duración", value=song.get('duration', 'Desconocida'), inline=True)
            embed.add_field(name="👤 Solicitado por", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error reproduciendo: {str(e)}")
            await self.play_next(ctx)
    
    @commands.command(name='join', aliases=['j'])
    async def join(self, ctx):
        """Bot se une al canal de voz"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"✅ Unido a **{channel.name}**")
        else:
            await ctx.send("❌ Debes estar en un canal de voz")
    
    @commands.command(name='leave', aliases=['l', 'salir'])
    async def leave(self, ctx):
        """Bot sale del canal de voz"""
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].clear()
            await ctx.send("👋 Adiós!")
        else:
            await ctx.send("❌ No estoy en un canal de voz")
    
    @commands.command(name='play', aliases=['p', 'tocar'])
    async def play(self, ctx, *, query: str):
        """Reproduce música de YouTube"""
        if not ctx.guild.voice_client:
            await ctx.invoke(self.join)
        
        # Buscar canciones
        results = await self.search_youtube(query)
        if not results:
            return await ctx.send("❌ No se encontraron resultados")
        
        # Crear cola si no existe
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = deque()
        
        queue = self.queues[ctx.guild.id]
        
        # Agregar primera canción
        song_info = results[0]
        song = {
            'title': song_info.get('title', 'Desconocido'),
            'url': song_info['url'],
            'duration': song_info.get('duration', 0),
            'thumbnail': song_info.get('thumbnail')
        }
        queue.append(song)
        
        embed = discord.Embed(
            title="➕ Canción agregada a la cola",
            description=f"**[{song['title']}]({song['url']})**",
            color=0x0099ff
        )
        
        if len(queue) > 1:
            embed.add_field(name="📋 Posición en cola", value=len(queue), inline=True)
        embed.add_field(name="👤 Solicitado por", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        
        # Reproducir si no está reproduciendo
        if not ctx.guild.voice_client.is_playing():
            await self.play_next(ctx)
    
    @commands.command(name='queue', aliases=['q', 'cola'])
    async def queue(self, ctx):
        """Muestra la cola de reproducción"""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("📭 La cola está vacía")
        
        queue = list(self.queues[ctx.guild.id])[:10]
        embed = discord.Embed(title="📋 Cola de reproducción", color=0xffaa00)
        
        for i, song in enumerate(queue, 1):
            duration = f"{song.get('duration', 0)//60}:{song.get('duration', 0)%60:02d}" if song.get('duration') else "??:??"
            embed.add_field(
                name=f"{i}. {song['title'][:50]}...",
                value=f"`{duration}`", 
                inline=False
            )
        
        if len(self.queues[ctx.guild.id]) > 10:
            embed.set_footer(text=f"y {len(self.queues[ctx.guild.id]) - 10} más...")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        """Salta la canción actual"""
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏭️ Canción saltada")
        else:
            await ctx.send("⏹️ No hay nada reproduciéndose")
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pausa la música"""
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Pausado")
        else:
            await ctx.send("⏹️ No hay nada reproduciéndose")
    
    @commands.command(name='resume')
    async def resume(self, ctx):
        """Reanuda la música"""
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Reanudado")
        else:
            await ctx.send("🔴 No está pausado")
    
    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, vol: int = None):
        """Controla el volumen (0-100)"""
        voice_client = ctx.guild.voice_client
        if not voice_client:
            return await ctx.send("❌ No estoy en un canal de voz")
        
        if vol is None:
            current_vol = int(voice_client.source.volume * 100)
            return await ctx.send(f"🔊 Volumen actual: **{current_vol}%**")
        
        if 0 <= vol <= 100:
            voice_client.source.volume = vol / 100
            await ctx.send(f"🔊 Volumen ajustado: **{vol}%**")
        else:
            await ctx.send("❌ Volumen debe estar entre 0-100")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))