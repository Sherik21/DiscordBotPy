import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class BackCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="back",
        description="Return to the previous track."
    )
    async def back(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)

        if music_handler.history_empty:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "back.history_empty"),
                ephemeral=True
            )
            return

        music_handler.back_flag = True

        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "back.returned")
        )

        if voice and not voice.is_playing() and not music_handler.is_playing:
            await music_handler.player(voice=voice)

async def setup(bot):
    await bot.add_cog(BackCommand(bot))
