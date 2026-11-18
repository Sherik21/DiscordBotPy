import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class StopCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stop", description="Stop playback and clear current track.")
    async def stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)

        if not voice or (not voice.is_playing() and not voice.is_paused() and not music_handler.is_playing):
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "stop.nothing_playing"),
                ephemeral=True
            )
            return

        music_handler.clear()
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(guild_id, "stop.stopped")
        )

async def setup(bot):
    await bot.add_cog(StopCommand(bot))
