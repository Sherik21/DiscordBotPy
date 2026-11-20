import discord
from discord.ext import commands
from discord import app_commands

class JoinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="join",
        description="Connect the bot to your voice channel.",
        description_localizations={
            discord.Locale.russian: "Подключить бота к вашему голосовому каналу."
        }
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
                await channel.connect(timeout=20.0, reconnect=True)
                await interaction.followup.send(
                    content=self.bot.locale_manager.get_text(interaction, "join.joined", channel=str(channel.name)),
                    ephemeral=True
                )
        except Exception as error:
            print(f"Join error: {error}")
            await interaction.followup.send(
                content=self.bot.locale_manager.get_text(interaction, "common.error", error=str(error)),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(JoinCommand(bot))
