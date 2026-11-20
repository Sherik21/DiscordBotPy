import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler
from utils.utils import formatDuration, createProgressBar
from utils.ui import MusicControlView

class NowPlayingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="nowplaying",
        description="Show currently playing track.",
        description_localizations={
            discord.Locale.russian: "Показать текущий играющий трек."
        }
    )
    async def nowplaying(self, interaction: discord.Interaction):
        await self._send_now_playing(interaction)

    @app_commands.command(
        name="np",
        description="Alias for nowplaying.",
        description_localizations={
            discord.Locale.russian: "Показать текущий играющий трек."
        }
    )
    async def np(self, interaction: discord.Interaction):
        await self._send_now_playing(interaction)

    async def _send_now_playing(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current_track = music_handler.get_current_track()

        if not current_track or current_track.empty:
            await interaction.response.send_message(
                content=self.bot.locale_manager.get_text(interaction, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        elapsed_sec = music_handler.get_playback_position()
        total_sec = current_track.duration
        progress_bar = createProgressBar(elapsed_sec, total_sec)
        time_display = f"`{formatDuration(elapsed_sec)}` {progress_bar} `{formatDuration(total_sec)}`"

        embed = discord.Embed(
            title=current_track.title,
            url=current_track.url,
            color=0x5865F2
        )
        embed.add_field(name="Author", value=current_track.author or "Unknown", inline=True)
        embed.add_field(name="Volume", value=f"{music_handler.get_volume()}%", inline=True)
        embed.add_field(name="Progress", value=time_display, inline=False)

        if current_track.thumbnail:
            embed.set_thumbnail(url=current_track.thumbnail)

        view = MusicControlView(self.bot, interaction)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(NowPlayingCommand(bot))
