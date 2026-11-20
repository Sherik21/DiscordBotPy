import os
import struct
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
import discord
from discord.ext import commands
from discord.voice_state import VoiceConnectionState
from discord.gateway import DiscordVoiceWebSocket
from handler.music_handler import MusicHandler
from cogs.locales.locale_manager import LocaleManager

orig_execute_transition = VoiceConnectionState._execute_transition

async def patched_execute_transition(self, transition_id: int):
    if transition_id not in self.dave_pending_transitions:
        self.dave_pending_transitions[transition_id] = self.dave_protocol_version
    if self.dave_session:
        try:
            self.dave_session.prepare_transition(transition_id, self.dave_protocol_version)
        except Exception:
            pass
        try:
            self.dave_session.execute_transition(transition_id)
        except Exception:
            pass
    await orig_execute_transition(self, transition_id)

VoiceConnectionState._execute_transition = patched_execute_transition

orig_voice_ws_received_message = DiscordVoiceWebSocket.received_message

async def patched_voice_ws_received_message(self, msg):
    res = await orig_voice_ws_received_message(self, msg)
    if msg.get("op") == DiscordVoiceWebSocket.DAVE_EXECUTE_TRANSITION:
        tid = msg.get("d", {}).get("transition_id")
        state = self._connection
        sess = getattr(state, "dave_session", None)
        if sess and tid is not None:
            try:
                sess.prepare_transition(tid, state.dave_protocol_version)
            except Exception:
                pass
            try:
                sess.execute_transition(tid)
            except Exception:
                pass
    return res

DiscordVoiceWebSocket.received_message = patched_voice_ws_received_message

orig_voice_ws_received_binary_message = DiscordVoiceWebSocket.received_binary_message

async def patched_voice_ws_received_binary_message(self, msg: bytes):
    await orig_voice_ws_received_binary_message(self, msg)
    if len(msg) > 2:
        op = msg[2]
        if op in (DiscordVoiceWebSocket.MLS_ANNOUNCE_COMMIT_TRANSITION, DiscordVoiceWebSocket.MLS_WELCOME):
            tid = struct.unpack_from(">H", msg, 3)[0]
            state = self._connection
            sess = getattr(state, "dave_session", None)
            if tid == 0 and sess and not sess.ready:
                try:
                    sess.prepare_transition(0, state.dave_protocol_version)
                except Exception:
                    pass
                try:
                    sess.execute_transition(0)
                except Exception:
                    pass

DiscordVoiceWebSocket.received_binary_message = patched_voice_ws_received_binary_message

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        if not discord.opus.is_loaded():
            try:
                discord.opus._load_default()
            except Exception as opus_err:
                print(f"Failed to load opus: {opus_err}")
        self.__musicHandlers = {}
        self.locale_manager = LocaleManager(self)
        self.base_dir = Path(__file__).resolve().parent.parent
        self.__TOKEN = self.load_token()

    async def getMusicHandler(self, guild_id: int) -> MusicHandler:
        if guild_id not in self.__musicHandlers:
            self.__musicHandlers[guild_id] = MusicHandler(self)
        return self.__musicHandlers[guild_id]

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = member.guild.id
        if member == self.user:
            if before.channel and not after.channel:
                if guild_id in self.__musicHandlers:
                    self.__musicHandlers[guild_id].clear()
            return

        voice = member.guild.voice_client
        if voice and before.channel and voice.channel == before.channel:
            non_bots = [m for m in before.channel.members if not m.bot]
            if len(non_bots) == 0:
                if guild_id in self.__musicHandlers:
                    self.__musicHandlers[guild_id].clear()
                await voice.disconnect()

    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash command(s).")
        except Exception as error:
            print(f"Failed to sync slash commands: {error}")
        print("LIFEHOSTING_APP_READY")

    async def load(self):
        cogs_dir = self.base_dir / "cogs"
        for entry in os.listdir(cogs_dir):
            if entry.endswith(".py") and not entry.startswith("__"):
                module_name = entry[:-3]
                try:
                    await self.load_extension(f"cogs.{module_name}")
                    print(f"Loaded cog: {module_name}")
                except Exception as error:
                    print(f"Failed to load cog {module_name}: {error}")

    def load_token(self) -> str:
        env_path = self.base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            values = dotenv_values(env_path)
            token = values.get("TOKEN")
            if token:
                return token.strip()
        env_token = os.getenv("TOKEN")
        return env_token.strip() if env_token else ""

    async def run(self):
        if not self.__TOKEN:
            print("Token is missing. Specify TOKEN in .env or set environment variable.")
            return
        async with self:
            await self.load()
            await self.start(self.__TOKEN)
