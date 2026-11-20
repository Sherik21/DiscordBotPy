import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class PauseCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="pause",
        description="Pause current playback.",
        description_localizations={
            discord.Locale.russian: "Приостановить воспроизведение."
        }
    )
    async def pause(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        if voice.is_paused():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "pause.already_paused"),
                ephemeral=True
            )
            return

        if not voice.is_playing():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "pause.not_playing"),
                ephemeral=True
            )
            return

        voice.pause()
        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "pause.paused")
        )

    @app_commands.command(
        name="resume",
        description="Resume paused playback.",
        description_localizations={
            discord.Locale.russian: "Возобновить воспроизведение."
        }
    )
    async def resume(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        if not voice.is_paused():
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "pause.not_paused"),
                ephemeral=True
            )
            return

        voice.resume()
        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "pause.resumed")
        )

async def setup(bot):
    await bot.add_cog(PauseCommand(bot))
