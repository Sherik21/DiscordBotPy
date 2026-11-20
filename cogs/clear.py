import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class ClearCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="clear",
        description="Clear all tracks from the queue."
    )
    async def clear(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)

        if music_handler.queue_empty:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "queue.queue_empty"),
                ephemeral=True
            )
            return

        removed_count = music_handler.clear_queue()
        await interaction.response.send_message(
            content=self.bot.locale_manager.get_text(interaction, "clear.cleared", count=removed_count)
        )

async def setup(bot):
    await bot.add_cog(ClearCommand(bot))
