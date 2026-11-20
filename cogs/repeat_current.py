import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler
from handler.queue_manager import RepeatMode

class RepeatCurrentCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="repeat_one",
        description="Toggle repeat mode for current track.",
        description_localizations={
            discord.Locale.russian: "Включить/выключить повтор текущего трека."
        }
    )
    async def repeat_current(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        new_mode = music_handler.toggle_repeat_mode(RepeatMode.ONE)

        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, new_mode.status_message)
        )

async def setup(bot):
    await bot.add_cog(RepeatCurrentCommand(bot))
