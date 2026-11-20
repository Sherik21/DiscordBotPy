import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class LeaveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="leave",
        description="Disconnect the bot from the voice channel.",
        description_localizations={
            discord.Locale.russian: "Отключить бота от голосового канала."
        }
    )
    async def leave(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        music_handler.clear()

        if voice.is_playing() or voice.is_paused():
            voice.stop()
        await voice.disconnect()

        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "leave.left"),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(LeaveCommand(bot))
