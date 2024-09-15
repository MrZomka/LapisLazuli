import json
import re
import disnake
import yt_dlp
import asyncio
from disnake.ext import commands


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_states = {}

    def get_guild_state(self, guild_id):
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = {
                "queue": [],
                "is_playing": False,
                "current_song": None
            }
        return self.guild_states[guild_id]

    @commands.slash_command(description="Play music")
    async def play(self, inter, query: str):
        if not inter.author.voice or not inter.author.voice.channel:
            await inter.response.send_message("You need to be in a voice channel to play music.")
            return
        if inter.guild.voice_client:
            if inter.guild.voice_client and inter.guild.voice_client.channel != inter.author.voice.channel:
                await inter.response.send_message("You need to be in the same voice channel as the bot to play music.")
                return
        await inter.response.send_message("Downloading...")
        await self.play_music(inter, query)

    @commands.slash_command(description="Stop the queue")
    async def stop(self, inter):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)
        voice_client = inter.guild.voice_client

        if voice_client and voice_client.is_playing():
            state["queue"].clear()
            voice_client.stop()
            await inter.response.send_message("👋 Cleared the queue, stopping playing music. See you soon!")
        else:
            await inter.response.send_message("No song is currently playing.")

    @commands.slash_command(description="Remove a specific song")
    async def remove(self, inter, track: int):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)
        voice_client = inter.guild.voice_client

        if voice_client and voice_client.is_playing():
            if len(state["queue"]) >= track > 0:
                track_to_remove = state["queue"][track - 1]
                state["queue"].pop(track - 1)
                await inter.response.send_message(f"Removed **{track_to_remove[1]}** from queue!")
            else:
                await inter.response.send_message(f"There's no track number {track + 1}!")
        else:
            await inter.response.send_message("No song is currently playing.")

    @commands.slash_command(description="Move a specific song to a different position in queue")
    async def move(self, inter, move_from: int, move_to: int):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)
        voice_client = inter.guild.voice_client

        if voice_client and voice_client.is_playing():
            if len(state["queue"]) >= move_from > 0 and len(state["queue"]) >= move_to > 0:
                track_to_move = state["queue"][move_from - 1]
                state["queue"].pop(move_from - 1)
                state["queue"].insert(move_to - 1, track_to_move)
                await inter.response.send_message(
                    f"🎧 Moved **{track_to_move[1]}** from position {move_from} to position {move_to}.")
        else:
            await inter.response.send_message("No song is currently playing.")

    @commands.slash_command(description="Skip the current song")
    async def skip(self, inter):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)
        voice_client = inter.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await inter.response.send_message("Skipped the current song.")
        else:
            await inter.response.send_message("No song is currently playing.")

    @commands.slash_command(description="Show the current song")
    async def now_playing(self, inter):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)

        if state["current_song"]:
            song_title, requester = state["current_song"]
            await inter.response.send_message(f"▶ Now playing: **{song_title}** (Requested by {requester.mention})")
        else:
            await inter.response.send_message("No song is currently playing.")

    @commands.slash_command(description="Check the music queue")
    async def queue(self, inter):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)

        if state["queue"]:
            queued_songs = "\n".join([f"{idx + 1}. {song[1]} - Requested by {song[2].author.mention}" for idx, song in
                                      enumerate(state["queue"])])
            queue_embed = disnake.Embed(
                description=f"{queued_songs}",
                colour=0x3498DB,
            )
            await inter.response.send_message(
                f"**▶ {state['current_song'][0]}**\n♫ Current queue ~ {len(state['queue']) + 1} tracks",
                embed=queue_embed)
        else:
            await inter.response.send_message("The queue is empty.")

    async def play_music(self, inter, query):
        guild_id = inter.guild.id
        state = self.get_guild_state(guild_id)

        try:
            song_list = await self.download_music(query)
            for song_file, title in song_list:
                state["queue"].append((song_file, title, inter))
            if len(song_list) > 1:
                await inter.edit_original_response(f"🎵 Added **{len(song_list)}** songs to the queue!")
            else:
                await inter.edit_original_response(
                    f"🎵 Added **{song_list[0][1]}** to the queue at position {len(state['queue'])}!")

            if not state["is_playing"]:
                await self.play_next_song(inter.guild.id)
        except Exception as e:
            print(f"Error: {e}")
            await inter.followup.send(f"An error occurred: `{e}`")

    async def play_next_song(self, guild_id):
        state = self.get_guild_state(guild_id)

        if len(state["queue"]) > 0:
            song_file, title, inter = state["queue"].pop(0)

            voice_client = inter.guild.voice_client

            if not voice_client:
                if inter.author.voice:
                    voice_channel = inter.author.voice.channel
                else:
                    await inter.followup.send("Error: Not in a voice channel. Try again.")
                    return

                voice_client = await voice_channel.connect()

            state["is_playing"] = True
            state["current_song"] = (title, inter.author)

            voice_client.play(disnake.FFmpegOpusAudio(song_file),
                              after=lambda e: self.bot.loop.create_task(self.song_finished(inter.guild)))

            await inter.followup.send(f"🎶 Now playing **{title}**! (Requested by {inter.author.mention})")
        else:
            state["is_playing"] = False
            state["current_song"] = None

    async def song_finished(self, guild):
        guild_id = guild.id
        state = self.get_guild_state(guild_id)

        if len(state["queue"]) > 0:
            self.bot.loop.create_task(self.play_next_song(guild_id))
        else:
            state["is_playing"] = False
            state["current_song"] = None

            voice_client = disnake.utils.get(self.bot.voice_clients, guild=guild)
            if voice_client:
                await voice_client.disconnect()

    async def download_music(self, query):
        ydl_opts = {
            'format': 'opus/bestaudio/best',
            'outtmpl': './temp/%(title)s [%(id)s].%(ext)s',
            'addmetadata': True,
            'postprocessors': [{
                'key': 'FFmpegMetadata',
            }]
        }

        http_regex = r"^(?:https?:\/\/)?(www\.)?[\w\-]+(\.[\w\-]+)+([\/\w\-._~:?#@!$&'()*+,;=%]*)?"
        with open('config.json') as f:
            config = json.load(f)

        if config.get("use-oauth-plugin"):
            youtube_regex = r"^(?:https?:\/\/)?(?:www\.)?(youtu\.be\/[a-zA-Z0-9_-]+|youtube\.[a-zA-Z]{2,3}\/[a-zA-Z0-9_-]+)"
            if re.findall(youtube_regex, query) or not re.findall(http_regex, query):
                ydl_opts.update({
                    'username': 'oauth2',
                    'password': '',
                })
            if not re.findall(http_regex, query):
                query = f"ytsearch:{query}"
        elif not re.findall(http_regex, query):
            query = f"ytsearch:{query}"

        def download(query_int):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query_int, download=True)
                media_type = info.get('_type', 'video')

                if media_type == 'playlist':
                    if not info['entries']:
                        print(f"Playlist is empty: {info['title']}")
                        return []
                    print(f"Downloading playlist: {info['title']}")
                    playlist_files = [(ydl.prepare_filename(video), video['title']) for video in info['entries']]
                    return playlist_files
                elif media_type == 'video':
                    song_file = ydl.prepare_filename(info)
                    title = info['title']
                    return [(song_file, title)]

        song_list = await asyncio.to_thread(download, query)
        return song_list if song_list else None


def setup(bot):
    bot.add_cog(Music(bot))
