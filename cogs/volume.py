import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class VolumeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="volume",
        description="Set playback volume (1-100%).",
        description_localizations={
            discord.Locale.russian: "Настроить громкость воспроизведения (1-100%)."
        }
    )
    @app_commands.describe(level="Volume level from 1 to 100.")
    async def volume(self, interaction: discord.Interaction, level: app_commands.Range[int, 1, 100] | None = None):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        voice = interaction.guild.voice_client

        if level is None:
            current_vol = music_handler.get_volume()
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "volume.current", volume=current_vol),
                ephemeral=True
            )
            return

        applied = music_handler.set_volume(level, voice)
        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "volume.changed", volume=applied)
        )

async def setup(bot):
    await bot.add_cog(VolumeCommand(bot))
