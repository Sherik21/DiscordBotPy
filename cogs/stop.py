import discord
from discord.ext import commands
from discord import app_commands
from handler.music_handler import MusicHandler

class StopCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _execute_stop(self, responder, user: discord.Member, guild: discord.Guild, target=None):
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

        if not voice or (not voice.is_playing() and not voice.is_paused() and not music_handler.is_playing):
            await responder(
                content=self.bot.locale_manager.get_text(target, "stop.nothing_playing"),
                ephemeral=True
            )
            return

        music_handler.clear()
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await responder(
            content=self.bot.locale_manager.get_text(target, "stop.stopped")
        )

    @app_commands.command(
        name="stop",
        description="Stop playback and clear current track.",
        description_localizations={
            discord.Locale.russian: "Остановить воспроизведение и очистить очередь."
        }
    )
    async def stop(self, interaction: discord.Interaction):
        async def responder(*args, **kwargs):
            return await interaction.response.send_message(*args, **kwargs)
        await self._execute_stop(responder, interaction.user, interaction.guild, target=interaction)

    @commands.command(name="stop")
    async def stop_prefix(self, ctx: commands.Context):
        async def responder(*args, **kwargs):
            kwargs.pop("ephemeral", None)
            return await ctx.send(*args, **kwargs)
        await self._execute_stop(responder, ctx.author, ctx.guild, target=ctx)

async def setup(bot):
    await bot.add_cog(StopCommand(bot))
