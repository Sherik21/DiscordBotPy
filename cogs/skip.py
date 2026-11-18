import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class SkipCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skip", description="Skip the current track.")
    async def skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current = music_handler.get_current_track()

        if not voice or (not voice.is_playing() and (not current or current.empty)):
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(guild_id, "skip.nothing_to_skip"),
                ephemeral=True
            )
            return

        music_handler.skip_flag = True
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(guild_id, "skip.skipped")
        )

        if not voice.is_playing() and not music_handler.is_playing:
            await music_handler.player(voice=voice)

async def setup(bot):
    await bot.add_cog(SkipCommand(bot))
