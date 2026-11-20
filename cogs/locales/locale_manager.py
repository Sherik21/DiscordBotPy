import json
import os
from pathlib import Path
from typing import Dict, Union, Optional
import discord

class LocaleManager:
    def __init__(self, bot):
        self.bot = bot
        self.locales: Dict[str, Dict] = {}
        self.guild_locales: Dict[int, str] = {}
        self.locales_path = Path(__file__).resolve().parent
        self._load_locales()
        self._load_guild_settings()

    def _load_locales(self):
        for entry in os.listdir(self.locales_path):
            if not entry.endswith(".json") or entry == "guild_settings.json":
                continue
            file_path = self.locales_path / entry
            if file_path.is_file():
                lang_code = entry.replace(".json", "")
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        self.locales[lang_code] = json.load(file)
                except Exception as error:
                    print(f"Failed to load locale {lang_code}: {error}")

    def _load_guild_settings(self):
        settings_file = self.locales_path / "guild_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as file:
                    self.guild_locales = {int(k): v for k, v in json.load(file).items()}
            except Exception as error:
                print(f"Failed to load guild settings: {error}")

    def _save_guild_settings(self):
        settings_file = self.locales_path / "guild_settings.json"
        try:
            with open(settings_file, "w", encoding="utf-8") as file:
                json.dump(self.guild_locales, file, ensure_ascii=False, indent=2)
        except Exception as error:
            print(f"Failed to save guild settings: {error}")

    def get_guild_locale(self, guild_id: int) -> str:
        return self.guild_locales.get(guild_id, "eng")

    def set_guild_locale(self, guild_id: int, language: str) -> bool:
        if language in self.locales:
            self.guild_locales[guild_id] = language
            self._save_guild_settings()
            return True
        return False

    def resolve_locale(self, target) -> str:
        if target is None:
            return "eng"
        if isinstance(target, str):
            if target in self.locales:
                return target
            if target.lower().startswith("ru"):
                return "rus"
            return "eng"
        if isinstance(target, discord.Interaction):
            if hasattr(target, "locale") and target.locale:
                loc = str(target.locale).lower()
                if loc.startswith("ru"):
                    return "rus"
                return "eng"
            guild_id = target.guild_id if target.guild_id else (target.guild.id if target.guild else None)
            if guild_id:
                return self.get_guild_locale(guild_id)
            return "eng"
        if hasattr(target, "guild") and target.guild:
            return self.get_guild_locale(target.guild.id)
        if isinstance(target, int):
            return self.get_guild_locale(target)
        return "eng"

    def get_text(self, target, key: str, **kwargs) -> str:
        lang = self.resolve_locale(target)
        locale_data = self.locales.get(lang, self.locales.get("eng", {}))

        parts = key.split(".")
        value = locale_data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        if value is None:
            value = self.locales.get("eng", {})
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return key

        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return value if isinstance(value, str) else key

    def get_available_languages(self) -> Dict[str, str]:
        return {
            "eng": "English",
            "rus": "Русский"
        }
