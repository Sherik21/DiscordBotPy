import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class ShuffleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="shuffle",
        description="Shuffle tracks in the queue."
    )
    async def shuffle(self, interaction: discord.Interaction):
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

        success = music_handler.shuffle()
        if success:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "shuffle.shuffled")
            )
        else:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "shuffle.not_enough"),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ShuffleCommand(bot))
