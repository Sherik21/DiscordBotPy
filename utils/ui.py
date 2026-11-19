import discord
from handler.music_handler import MusicHandler

class MusicControlView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Pause / Resume", style=discord.ButtonStyle.secondary, emoji="⏯️")
    async def toggle_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        if voice.is_paused():
            voice.resume()
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "pause.resumed"),
                ephemeral=True
            )
        elif voice.is_playing():
            voice.pause()
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "pause.paused"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "pause.not_playing"),
                ephemeral=True
            )

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def skip_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()

        if not voice or (not voice.is_playing() and (not current or current.empty)):
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "skip.nothing_to_skip"),
                ephemeral=True
            )
            return

        music_handler.skip_flag = True
        voice.stop()
        await interaction.response.send_message(
            self.bot.locale_manager.get_text(self.guild_id, "skip.skipped"),
            ephemeral=True
        )

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def toggle_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        mode = music_handler.cycle_repeat_mode()
        text = self.bot.locale_manager.get_text(self.guild_id, mode.status_message)
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_playback(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)

        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "stop.nothing_playing"),
                ephemeral=True
            )
            return

        music_handler.clear()
        voice.stop()
        await interaction.response.send_message(
            self.bot.locale_manager.get_text(self.guild_id, "stop.stopped"),
            ephemeral=True
        )
