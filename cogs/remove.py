import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class RemoveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="remove",
        description="Remove a track from the queue by its number."
    )
    @app_commands.describe(index="Track position number in the queue.")
    async def remove(self, interaction: discord.Interaction, index: int):
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

        removed_track = music_handler.remove_track(index - 1)
        if removed_track:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "remove.removed", title=removed_track.title)
            )
        else:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "remove.invalid_index"),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(RemoveCommand(bot))
