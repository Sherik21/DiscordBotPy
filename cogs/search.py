import discord
from discord.ext import commands
from discord import app_commands
from handler.track import Track
from utils.utils import extractInfoByTitle, createEmbed
from handler.music_handler import MusicHandler
from utils.ui import MusicControlView

class SearchCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="search", description="Search and play audio by song title.")
    @app_commands.describe(title="The song title to search and play.")
    async def search(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()
        guild_id = interaction.guild.id

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(guild_id, "common.not_in_voice"),
                ephemeral=True
            )
            return

        user_channel = interaction.user.voice.channel
        voice = interaction.guild.voice_client

        if not voice:
            try:
                voice = await user_channel.connect(timeout=20.0, reconnect=True)
            except Exception as connect_error:
                print(f"Voice connect error: {connect_error}")
                await interaction.followup.send(
                    content=self.bot.locale_manager.get_text(guild_id, "join.cannot_join"),
                    ephemeral=True
                )
                return
        elif voice.channel != user_channel:
            try:
                await voice.move_to(user_channel)
            except Exception:
                pass

        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        music_handler.stop_flag = False

        try:
            track: Track = await extractInfoByTitle(title)
        except Exception as error:
            print(f"Track search error: {error}")
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(guild_id, "common.error", error=str(error)),
                ephemeral=True
            )
            return

        music_handler.add_track(track)
        embed = createEmbed(track=track)
        embed.add_field(
            name=self.bot.locale_manager.get_text(guild_id, "common.added_by"),
            value=f"<@{interaction.user.id}>",
            inline=False
        )

        view = MusicControlView(self.bot, guild_id)
        await interaction.followup.send(embed=embed, view=view)

        if voice.is_playing() or music_handler.is_playing:
            return

        await music_handler.player(voice=voice)

async def setup(bot):
    await bot.add_cog(SearchCommand(bot))
