import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler
from utils.utils import parseSeekPosition, formatDuration

class SeekCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _execute_seek(self, responder, user: discord.Member, guild: discord.Guild, position_input: str):
        guild_id = guild.id

        if not user.voice or not user.voice.channel:
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = guild.voice_client
        if not voice or not voice.is_connected():
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current_track = music_handler.get_current_track()
        if not current_track or current_track.empty:
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        current_pos = music_handler.get_playback_position()
        target_seconds = parseSeekPosition(position_input, current_pos)
        if target_seconds < 0 or (current_track.duration > 0 and target_seconds >= current_track.duration):
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "seek.invalid_position"),
                ephemeral=True
            )
            return

        success = await music_handler.seek(target_seconds, voice)
        if success:
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "seek.success", position=formatDuration(target_seconds))
            )
        else:
            await responder(
                content=self.bot.locale_manager.get_text(guild_id, "seek.failed"),
                ephemeral=True
            )

    @app_commands.command(name="seek", description="Seek to a position in current track.")
    @app_commands.describe(position="Timestamp (e.g. 1:30, 45, +15, -10).")
    async def seek(self, interaction: discord.Interaction, position: str):
        await interaction.response.defer()
        async def responder(*args, **kwargs):
            return await interaction.followup.send(*args, **kwargs)
        await self._execute_seek(responder, interaction.user, interaction.guild, position)

    @commands.command(name="seek")
    async def seek_prefix(self, ctx: commands.Context, *, position: str = ""):
        if not position.strip():
            return
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_seek(responder, ctx.author, ctx.guild, position.strip())

    @commands.command(name="forward", aliases=["ff"])
    async def forward_prefix(self, ctx: commands.Context, seconds: str = "15"):
        pos_str = f"+{seconds.strip()}" if not seconds.strip().startswith("+") else seconds.strip()
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_seek(responder, ctx.author, ctx.guild, pos_str)

    @commands.command(name="rewind", aliases=["rw"])
    async def rewind_prefix(self, ctx: commands.Context, seconds: str = "15"):
        pos_str = f"-{seconds.strip()}" if not seconds.strip().startswith("-") else seconds.strip()
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_seek(responder, ctx.author, ctx.guild, pos_str)

async def setup(bot):
    await bot.add_cog(SeekCommand(bot))
