import discord
from discord.ext import commands
from discord import app_commands
from handler.track import Track
from utils.utils import extractInfoByUrl, extractInfoByTitle, extractPlaylist, isValidUrl, isPlaylistUrl, createEmbed
from handler.music_handler import MusicHandler
from utils.ui import MusicControlView

class PlayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _execute_play(self, responder, user: discord.Member, guild: discord.Guild, query: str, target=None):
        target = target or guild.id
        guild_id = guild.id

        if not user.voice or not user.voice.channel:
            await responder(
                content=self.bot.locale_manager.get_text(target, "common.not_in_voice"),
                ephemeral=True
            )
            return

        user_channel = user.voice.channel
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        music_handler.stop_flag = False

        try:
            if await isValidUrl(query):
                if isPlaylistUrl(query):
                    tracks = await extractPlaylist(query)
                    if not tracks:
                        raise ValueError("Empty playlist")

                    bot_perms = user_channel.permissions_for(guild.me)
                    if not bot_perms.connect or not bot_perms.view_channel:
                        await responder(
                            content=self.bot.locale_manager.get_text(target, "join.missing_permissions"),
                            ephemeral=True
                        )
                        return

                    voice = guild.voice_client
                    if voice and not voice.is_connected():
                        try:
                            await voice.disconnect(force=True)
                        except Exception:
                            pass
                        voice = None

                    if not voice:
                        try:
                            voice = await user_channel.connect(timeout=20.0, reconnect=True, self_deaf=True)
                        except Exception as connect_error:
                            err_name = type(connect_error).__name__
                            err_str = str(connect_error).strip()
                            print(f"Voice connect error: {err_name} - {connect_error}", flush=True)
                            if isinstance(connect_error, discord.Forbidden):
                                msg = self.bot.locale_manager.get_text(target, "join.missing_permissions")
                            elif isinstance(connect_error, asyncio.TimeoutError) or err_name == "TimeoutError" or not err_str:
                                msg = self.bot.locale_manager.get_text(target, "join.timeout")
                            else:
                                msg = f"{self.bot.locale_manager.get_text(target, 'join.cannot_join')} ({err_str or err_name})"
                            await responder(content=msg, ephemeral=True)
                            return
                    elif voice.channel != user_channel:
                        try:
                            await voice.move_to(user_channel)
                        except Exception:
                            pass

                    music_handler.add_tracks(tracks)

                    embed = discord.Embed(
                        title=self.bot.locale_manager.get_text(target, "playlist.title"),
                        description=self.bot.locale_manager.get_text(target, "playlist.added", count=len(tracks)),
                        color=0x5865F2
                    )
                    embed.add_field(
                        name=self.bot.locale_manager.get_text(target, "common.added_by"),
                        value=f"<@{user.id}>",
                        inline=False
                    )
                    view = MusicControlView(self.bot, target)
                    await responder(embed=embed, view=view)

                    if not voice.is_playing() and not music_handler.is_playing:
                        await music_handler.player(voice=voice)
                    return
                else:
                    track: Track = await extractInfoByUrl(query)
            else:
                track: Track = await extractInfoByTitle(query)
        except Exception as error:
            print(f"Track extraction error: {error}")
            await responder(
                content=self.bot.locale_manager.get_text(target, "common.error", error=str(error)),
                ephemeral=True
            )
            return

        bot_perms = user_channel.permissions_for(guild.me)
        if not bot_perms.connect or not bot_perms.view_channel:
            await responder(
                content=self.bot.locale_manager.get_text(target, "join.missing_permissions"),
                ephemeral=True
            )
            return

        voice = guild.voice_client
        if voice and not voice.is_connected():
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass
            voice = None

        if not voice:
            try:
                voice = await user_channel.connect(timeout=20.0, reconnect=True, self_deaf=True)
            except Exception as connect_error:
                err_name = type(connect_error).__name__
                err_str = str(connect_error).strip()
                print(f"Voice connect error: {err_name} - {connect_error}", flush=True)
                if isinstance(connect_error, discord.Forbidden):
                    msg = self.bot.locale_manager.get_text(target, "join.missing_permissions")
                elif isinstance(connect_error, asyncio.TimeoutError) or err_name == "TimeoutError" or not err_str:
                    msg = self.bot.locale_manager.get_text(target, "join.timeout")
                else:
                    msg = f"{self.bot.locale_manager.get_text(target, 'join.cannot_join')} ({err_str or err_name})"
                await responder(content=msg, ephemeral=True)
                return
        elif voice.channel != user_channel:
            try:
                await voice.move_to(user_channel)
            except Exception:
                pass

        music_handler.add_track(track)
        embed = createEmbed(track=track)
        embed.add_field(
            name=self.bot.locale_manager.get_text(target, "common.added_by"),
            value=f"<@{user.id}>",
            inline=False
        )

        view = MusicControlView(self.bot, target)
        await responder(embed=embed, view=view)

        if not voice.is_playing():
            await music_handler.player(voice=voice)

    @app_commands.command(
        name="play",
        description="Play audio from a URL, playlist, or search query."
    )
    @app_commands.describe(query="The song URL, playlist link, or search title.")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        async def responder(*args, **kwargs):
            return await interaction.followup.send(*args, **kwargs)
        await self._execute_play(responder, interaction.user, interaction.guild, query, target=interaction)

    @commands.command(name="play")
    async def play_prefix(self, ctx: commands.Context, *, query: str = ""):
        if not query.strip():
            return
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_play(responder, ctx.author, ctx.guild, query.strip(), target=ctx)

async def setup(bot):
    await bot.add_cog(PlayCommand(bot))
