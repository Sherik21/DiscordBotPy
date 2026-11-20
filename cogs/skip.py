import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class SkipCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _execute_skip(self, responder, user: discord.Member, guild: discord.Guild, target=None):
        target = target or guild.id
        guild_id = guild.id

        if not user.voice or not user.voice.channel:
            await responder(
                content=self.bot.locale_manager.get_text(target, "common.not_in_voice"),
                ephemeral=True
            )
            return

        voice = guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(guild_id)
        current = music_handler.get_current_track()

        if not voice or (not voice.is_playing() and (not current or current.empty)):
            await responder(
                content=self.bot.locale_manager.get_text(target, "skip.nothing_to_skip"),
                ephemeral=True
            )
            return

        music_handler.skip_flag = True
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await responder(
            content=self.bot.locale_manager.get_text(target, "skip.skipped")
        )

        if not voice.is_playing() and not music_handler.is_playing:
            await music_handler.player(voice=voice)

    @app_commands.command(
        name="skip",
        description="Skip the current track.",
        description_localizations={
            discord.Locale.russian: "Пропустить текущий трек."
        }
    )
    async def skip(self, interaction: discord.Interaction):
        async def responder(*args, **kwargs):
            return await interaction.response.send_message(*args, **kwargs)
        await self._execute_skip(responder, interaction.user, interaction.guild, target=interaction)

    @commands.command(name="skip", aliases=["s"])
    async def skip_prefix(self, ctx: commands.Context):
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_skip(responder, ctx.author, ctx.guild, target=ctx)

async def setup(bot):
    await bot.add_cog(SkipCommand(bot))
