import discord
from handler.music_handler import MusicHandler
from utils.utils import formatDuration, parseSeekPosition

class SeekModal(discord.ui.Modal):
    def __init__(self, bot, target, guild_id: int):
        title = bot.locale_manager.get_text(target, "seek.modal_title")
        super().__init__(title=title)
        self.bot = bot
        self.guild_id = guild_id
        label_text = bot.locale_manager.get_text(target, "seek.modal_label")
        placeholder_text = bot.locale_manager.get_text(target, "seek.modal_placeholder")
        self.time_input = discord.ui.TextInput(
            label=label_text,
            placeholder=placeholder_text,
            required=True,
            max_length=15
        )
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        current_pos = music_handler.get_playback_position()
        target_seconds = parseSeekPosition(self.time_input.value, current_pos)
        if target_seconds < 0 or (current.duration > 0 and target_seconds >= current_track_dur(current)):
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.invalid_position"),
                ephemeral=True
            )
            return

        ok = await music_handler.seek(target_seconds, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.success", position=formatDuration(target_seconds)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.failed"),
                ephemeral=True
            )

def current_track_dur(track):
    return track.duration if track else 0

class MusicControlView(discord.ui.View):
    def __init__(self, bot, target):
        super().__init__(timeout=None)
        self.bot = bot
        if isinstance(target, int):
            self.guild_id = target
        elif hasattr(target, "guild") and target.guild:
            self.guild_id = target.guild.id
        elif hasattr(target, "guild_id") and target.guild_id:
            self.guild_id = target.guild_id
        else:
            self.guild_id = 0
        btn_label = bot.locale_manager.get_text(target, "seek.button_label")
        if btn_label:
            self.open_seek_modal.label = btn_label

    @discord.ui.button(label="Pause / Resume", style=discord.ButtonStyle.secondary, emoji="⏯️", row=0)
    async def toggle_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        if voice.is_paused():
            voice.resume()
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "pause.resumed"),
                ephemeral=True
            )
        elif voice.is_playing():
            voice.pause()
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "pause.paused"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "pause.not_playing"),
                ephemeral=True
            )

    @discord.ui.button(label="-15s", style=discord.ButtonStyle.secondary, emoji="⏪", row=0)
    async def rewind_15(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        ok, target_pos = await music_handler.seek_relative(-15, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.success", position=formatDuration(target_pos)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.failed"),
                ephemeral=True
            )

    @discord.ui.button(label="+15s", style=discord.ButtonStyle.secondary, emoji="⏩", row=0)
    async def forward_15(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_connected():
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "common.bot_not_in_voice"),
                ephemeral=True
            )
            return

        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()
        if not current or current.empty:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "queue.nothing_playing"),
                ephemeral=True
            )
            return

        ok, target_pos = await music_handler.seek_relative(15, voice)
        if ok:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.success", position=formatDuration(target_pos)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "seek.failed"),
                ephemeral=True
            )

    @discord.ui.button(label="Указать время", style=discord.ButtonStyle.secondary, emoji="⏱️", row=0)
    async def open_seek_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SeekModal(self.bot, interaction, self.guild_id))

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️", row=0)
    async def skip_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        current = music_handler.get_current_track()

        if not voice or (not voice.is_playing() and (not current or current.empty)):
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "skip.nothing_to_skip"),
                ephemeral=True
            )
            return

        music_handler.skip_flag = True
        voice.stop()
        await interaction.response.send_message(
            self.bot.locale_manager.get_text(interaction, "skip.skipped"),
            ephemeral=True
        )

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary, emoji="🔁", row=1)
    async def toggle_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)
        mode = music_handler.cycle_repeat_mode()
        text = self.bot.locale_manager.get_text(interaction, mode.status_message)
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=1)
    async def stop_playback(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client
        music_handler: MusicHandler = await self.bot.getMusicHandler(self.guild_id)

        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message(
                self.bot.locale_manager.get_text(interaction, "stop.nothing_playing"),
                ephemeral=True
            )
            return

        music_handler.clear()
        voice.stop()
        await interaction.response.send_message(
            self.bot.locale_manager.get_text(interaction, "stop.stopped"),
            ephemeral=True
        )
