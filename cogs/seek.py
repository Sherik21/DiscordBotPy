import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler
from utils.utils import parseTimeString, formatDuration

class SeekCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="seek", description="Seek to a position in current track.")
    @app_commands.describe(position="Target timestamp (seconds or mm:ss or hh:mm:ss).")
    async def seek(self, interaction: discord.Interaction, position: str):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current_track = music_handler.get_current_track()
        if not current_track or current_track.empty:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        seconds = parseTimeString(position)
        if seconds < 0 or (current_track.duration > 0 and seconds > current_track.duration):
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "seek.invalid_position"),
                ephemeral=True
            )
            return

        await interaction.response.defer()
        success = await music_handler.seek(seconds, voice)
        if success:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(guild_id, "seek.success", position=formatDuration(seconds))
            )
        else:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(guild_id, "seek.failed"),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(SeekCommand(bot))
