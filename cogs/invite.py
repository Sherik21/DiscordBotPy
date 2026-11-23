import discord
from discord.ext import commands
from discord import app_commands

class InviteCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="invite",
        description="Get bot invite link with all required permissions."
    )
    async def invite(self, interaction: discord.Interaction):
        client_id = self.bot.user.id if self.bot.user else 1205563193423036436
        invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={client_id}"
            f"&permissions=8&integration_type=0&scope=bot+applications.commands"
        )

        embed = discord.Embed(
            title="Invite NoNameMusic",
            description="Use the button below to add the bot to your server with full voice channel access.",
            color=0x5865F2
        )
        embed.add_field(
            name="Permissions Included",
            value="Administrator (full access to all voice and text channels)",
            inline=False
        )

        view = discord.ui.View()
        button = discord.ui.Button(
            label="Add to Server",
            url=invite_url,
            style=discord.ButtonStyle.link,
            emoji="🔗"
        )
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.command(name="invite")
    async def invite_prefix(self, ctx: commands.Context):
        client_id = self.bot.user.id if self.bot.user else 1205563193423036436
        invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={client_id}"
            f"&permissions=8&integration_type=0&scope=bot+applications.commands"
        )
        embed = discord.Embed(
            title="Invite NoNameMusic",
            description="Use the button below to add the bot to your server with full voice channel access.",
            color=0x5865F2
        )
        view = discord.ui.View()
        button = discord.ui.Button(
            label="Add to Server",
            url=invite_url,
            style=discord.ButtonStyle.link,
            emoji="🔗"
        )
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(InviteCommand(bot))
