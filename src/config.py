import json
import os
import logging
import sys
from typing import List, Set, Dict


class Config:
    """Handles loading and accessing application configuration.
    
    Reads configuration from a JSON file and provides property-based access
    to all configuration values with sensible defaults.
    """
    
    def __init__(self, filepath: str):
        """Initialize configuration from a JSON file.
        
        Args:
            filepath: Path to the configuration JSON file
            
        Raises:
            SystemExit: If file not found or JSON is invalid
        """
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        """Load and parse the configuration file.
        
        Returns:
            Parsed configuration dictionary
            
        Raises:
            SystemExit: If file not found or JSON parsing fails
        """
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
        """Discord webhook URL for sending notifications."""
        return self._data.get('discord_webhook_url', '')

    @property
    def monitored_threads(self) -> List[str]:
        """List of forum thread URLs to monitor."""
        return self._data.get('monitored_threads', [])

    @property
    def active_players(self) -> Set[str]:
        """Set of active player usernames to track."""
        return set(self._data.get('active_players', []))

    @property
    def game_masters(self) -> List[str]:
        """List of Game Master usernames whose posts trigger player reminders."""
        return self._data.get('game_masters', [])

    @property
    def threshold_days(self) -> int:
        """Number of days before sending inactivity reminder."""
        return self._data.get('inactivity_threshold_days', 5)

    @property
    def selectors(self) -> Dict[str, str]:
        """CSS selectors for scraping forum pages."""
        return self._data.get('selectors', {})

    @property
    def player_discord_role_ids(self) -> Dict[str, str]:
        """Mapping of player names to Discord role IDs for mentions."""
        return self._data.get('player_discord_role_ids', {})

    @property
    def check_interval_minutes(self) -> int:
        """Interval in minutes between activity checks (for continuous mode)."""
        return self._data.get('check_interval_minutes', 1440)

    @property
    def daily_run_time(self) -> str:
        """Time of day to run daily check (HH:MM format)."""
        return self._data.get('daily_run_time', "10:00")

    @property
    def player_images(self) -> Dict[str, str]:
        """Mapping of player names to image file paths for reminders."""
        return self._data.get('player_images', {})

    @property
    def image_threshold_days(self) -> int:
        """Minimum days of inactivity before attaching player images."""
        return self._data.get('image_threshold_days', 7)

    @property
    def overseer_image(self) -> str:
        """Image file path for the overseer (header) message."""
        return self._data.get('overseer_image', 'overseer.png')

    @property
    def overseer_message(self) -> str:
        """Header message sent before player reminders."""
        default_msg = "**Nadzorca rozpoczyna inspekcję aktywności...**"
        return self._data.get('overseer_message', default_msg)
