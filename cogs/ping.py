import discord
from discord.ext import commands
from discord import app_commands

class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Show bot latency.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()

        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Ping", description="Gateway latency", color=discord.Color.blue())
        embed.add_field(name="Latency", value=f"{latency_ms} ms", inline=False)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PingCommand(bot))
