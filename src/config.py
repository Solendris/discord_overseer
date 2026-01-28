import json
import os
import logging
import sys
from typing import List, Set, Dict

class Config:
    """Handles loading and accessing application configuration."""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.filepath):
            logging.error(f"Config file {self.filepath} not found.")
            sys.exit(1)
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from {self.filepath}: {e}")
            sys.exit(1)

    @property
    def webhook_url(self) -> str:
        return self._data.get('discord_webhook_url', '')

    @property
    def monitored_threads(self) -> List[str]:
        return self._data.get('monitored_threads', [])

    @property
    def active_players(self) -> Set[str]:
        return set(self._data.get('active_players', []))

    @property
    def excluded_users(self) -> List[str]:
        return self._data.get('excluded_users', [])

    @property
    def threshold_days(self) -> int:
        return self._data.get('inactivity_threshold_days', 5)

    @property
    def selectors(self) -> dict:
        return self._data.get('selectors', {})

    @property
    def player_discord_role_ids(self) -> Dict[str, str]:
        return self._data.get('player_discord_role_ids', {})

    @property
    def check_interval_minutes(self) -> int:
        return self._data.get('check_interval_minutes', 1440)

    @property
    def daily_run_time(self) -> str:
        return self._data.get('daily_run_time', "10:00")

    @property
    def player_images(self) -> Dict[str, str]:
        return self._data.get('player_images', {})

    @property
    def image_threshold_days(self) -> int:
        return self._data.get('image_threshold_days', 7)

    @property
    def overseer_image(self) -> str:
        return self._data.get('overseer_image', 'overseer.png')

    @property
    def overseer_message(self) -> str:
        default_msg = "**Nadzorca rozpoczyna inspekcję aktywności...**"
        return self._data.get('overseer_message', default_msg)
