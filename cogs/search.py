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

    @app_commands.command(
        name="search",
        description="Search and play audio by song title."
    )
    @app_commands.describe(title="The song title to search and play.")
    async def search(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()
        guild_id = interaction.guild.id

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        user_channel = interaction.user.voice.channel
        bot_perms = user_channel.permissions_for(interaction.guild.me)
        if not bot_perms.connect or not bot_perms.view_channel:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(interaction, "join.missing_permissions"),
                ephemeral=True
            )
            return

        voice = interaction.guild.voice_client
        if voice and not voice.is_connected():
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass
            voice = None

        if not voice:
            try:
                voice = await user_channel.connect(timeout=20.0, reconnect=True, self_deaf=True)
            except Exception as connect_error:
                err_name = type(connect_error).__name__
                err_str = str(connect_error).strip()
                print(f"Voice connect error: {err_name} - {connect_error}", flush=True)
                if isinstance(connect_error, discord.Forbidden):
                    msg = self.bot.locale_manager.get_text(interaction, "join.missing_permissions")
                elif isinstance(connect_error, asyncio.TimeoutError) or err_name == "TimeoutError" or not err_str:
                    msg = self.bot.locale_manager.get_text(interaction, "join.timeout")
                else:
                    msg = f"{self.bot.locale_manager.get_text(interaction, 'join.cannot_join')} ({err_str or err_name})"
                await interaction.followup.send(content=msg, ephemeral=True)
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
                content=self.bot.locale_manager.get_text(interaction, "common.error", error=str(error)),
                ephemeral=True
            )
            return

        music_handler.add_track(track)
        embed = createEmbed(track=track)
        embed.add_field(
            name=self.bot.locale_manager.get_text(interaction, "common.added_by"),
            value=f"<@{interaction.user.id}>",
            inline=False
        )

        view = MusicControlView(self.bot, interaction)
        await interaction.followup.send(embed=embed, view=view)

        if voice.is_playing() or music_handler.is_playing:
            return

        await music_handler.player(voice=voice)

async def setup(bot):
    await bot.add_cog(SearchCommand(bot))
