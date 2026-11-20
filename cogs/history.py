import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler
from utils.utils import formatDuration

class HistoryCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="history",
        description="Show playback history."
    )
    async def history(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        await interaction.response.defer()

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current_track = music_handler.get_current_track()
        history_list = music_handler.get_history()

        embed = discord.Embed(
            title=self.bot.locale_manager.get_text(interaction, "queue.title_history"),
            color=0x5865F2
        )

        if not current_track or current_track.empty:
            embed.description = self.bot.locale_manager.get_text(interaction, "queue.nothing_playing") + "\n"
        else:
            embed.description = (
                self.bot.locale_manager.get_text(interaction, "queue.currently_playing")
                + f"\n[{current_track.title}]({current_track.url}) `[{formatDuration(current_track.duration)}]`\n"
            )
            if current_track.thumbnail:
                embed.set_thumbnail(url=current_track.thumbnail)

        if not history_list:
            embed.add_field(
                name=self.bot.locale_manager.get_text(interaction, "queue.previous_in_list"),
                value=self.bot.locale_manager.get_text(interaction, "queue.history_empty"),
                inline=False
            )
        else:
            total_seconds = sum(t.duration for t in history_list)
            total_duration_str = formatDuration(total_seconds)

            display_history = history_list[:10]
            lines = []
            for i, item in enumerate(display_history):
                dur = formatDuration(item.duration)
                title = item.title[:50] + "..." if len(item.title) > 53 else item.title
                lines.append(f"`{i+1}.` [{title}]({item.url}) `[{dur}]`")

            history_str = "\n".join(lines)
            if len(history_list) > 10:
                count = len(history_list) - 10
                history_str += "\n\n" + self.bot.locale_manager.get_text(
                    interaction,
                    "queue.and_another",
                    count=count,
                    type=self.bot.locale_manager.get_text(interaction, "queue.type_history")
                )

            embed.add_field(
                name=f"{self.bot.locale_manager.get_text(interaction, 'queue.previous_in_list')} ({self.bot.locale_manager.get_text(interaction, 'queue.total')}: {total_duration_str})",
                value=history_str,
                inline=False
            )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HistoryCommand(bot))
