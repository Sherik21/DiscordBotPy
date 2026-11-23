import discord
from discord.ext import commands
from discord import app_commands

class JoinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="join",
        description="Connect the bot to your voice channel."
    )
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(interaction, "common.not_in_voice"),
                ephemeral=True
            )
            return

        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client and not voice_client.is_connected():
            try:
                await voice_client.disconnect(force=True)
            except Exception:
                pass
            voice_client = None

        try:
            if voice_client:
                if voice_client.channel == channel:
                    await interaction.followup.send(
                        content=self.bot.locale_manager.get_text(interaction, "join.already_in_channel", channel=str(channel.name)),
                        ephemeral=True
                    )
                else:
                    await voice_client.move_to(channel)
                    await interaction.followup.send(
                        content=self.bot.locale_manager.get_text(interaction, "join.joined", channel=str(channel.name)),
                        ephemeral=True
                    )
            else:
                voice_client = await channel.connect(timeout=20.0, reconnect=True, self_deaf=True)
                await interaction.followup.send(
                    content=self.bot.locale_manager.get_text(interaction, "join.joined", channel=str(channel.name)),
                    ephemeral=True
                )

            music_handler = await self.bot.getMusicHandler(interaction.guild.id)
            if voice_client and not music_handler.is_playing:
                music_handler.start_idle_timer(voice_client)
        except Exception as error:
            print(f"Join error: {error}")
            if isinstance(error, discord.Forbidden):
                msg = self.bot.locale_manager.get_text(interaction, "join.missing_permissions")
            else:
                msg = f"{self.bot.locale_manager.get_text(interaction, 'join.cannot_join')} ({error})"
            await interaction.followup.send(content=msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(JoinCommand(bot))
