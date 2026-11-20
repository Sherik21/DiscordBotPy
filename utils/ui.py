import discord
from handler.music_handler import MusicHandler
from utils.utils import formatDuration, createProgressBar

class SeekSelect(discord.ui.Select):
    def __init__(self, bot, guild_id: int, duration: int):
        self.bot = bot
        self.guild_id = guild_id
        options = []
        percentages = [0.10, 0.25, 0.50, 0.75, 0.90]
        for p in percentages:
            sec = int(duration * p)
            bar = createProgressBar(sec, duration, length=10)
            options.append(
                discord.SelectOption(
                    label=f"{int(p * 100)}% ({formatDuration(sec)})",
                    value=str(sec),
                    description=bar,
                    emoji="⏱️"
                )
            )
        placeholder = self.bot.locale_manager.get_text(self.guild_id, "seek.placeholder")
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        target_seconds = int(self.values[0])
        ok = await music_handler.seek(target_seconds, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.success", position=formatDuration(target_seconds)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.failed"),
                ephemeral=True
            )

class MusicControlView(discord.ui.View):
    def __init__(self, bot, guild_id: int, duration: int = 0):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        if duration > 30:
            self.add_item(SeekSelect(bot, guild_id, duration))

    @discord.ui.button(label="Pause / Resume", style=discord.ButtonStyle.secondary, emoji="⏯️", row=0)
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

    @discord.ui.button(label="-15s", style=discord.ButtonStyle.secondary, emoji="⏪", row=0)
    async def rewind_15(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        ok, target_pos = await music_handler.seek_relative(-15, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.success", position=formatDuration(target_pos)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.failed"),
                ephemeral=True
            )

    @discord.ui.button(label="+15s", style=discord.ButtonStyle.secondary, emoji="⏩", row=0)
    async def forward_15(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        ok, target_pos = await music_handler.seek_relative(15, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.success", position=formatDuration(target_pos)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(self.guild_id, "seek.failed"),
                ephemeral=True
            )

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️", row=0)
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

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary, emoji="🔁", row=0)
    async def toggle_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        mode = music_handler.cycle_repeat_mode()
        text = self.bot.locale_manager.get_text(self.guild_id, mode.status_message)
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=2)
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
