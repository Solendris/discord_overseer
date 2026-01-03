import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Force UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

CONFIG_FILE = 'config.json'

@dataclass
class Post:
    username: str
    date: datetime

class Config:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.filepath):
            logging.error(f"Config file {self.filepath} not found.")
            sys.exit(1)
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

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
    def threshold_days(self) -> int:
        return self._data.get('inactivity_threshold_days', 5)

    @property
    def selectors(self) -> dict:
        return self._data.get('selectors', {})

class DateParser:
    @staticmethod
    def parse(date_str: str) -> Optional[datetime]:
        """
        Parses polish forum dates like:
        - "18-10-2025, 20:09"
        - "Dzisiaj, 14:30"
        - "Wczoraj, 09:12"
        - "1 godzinę temu"
        """
        now = datetime.now()
        date_str = date_str.strip().lower()

        if "temu" in date_str or "godzin" in date_str or "minut" in date_str:
            return now

        time_match = re.search(r'(\d{1,2}:\d{2})', date_str)
        if "dzisiaj" in date_str:
            if time_match:
                dt = datetime.strptime(time_match.group(1), "%H:%M")
                return now.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
            return now

        if "wczoraj" in date_str:
            yesterday = now - timedelta(days=1)
            if time_match:
                dt = datetime.strptime(time_match.group(1), "%H:%M")
                return yesterday.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
            return yesterday

        try:
            return datetime.strptime(date_str, "%d-%m-%Y, %H:%M")
        except ValueError:
            logging.warning(f"Could not parse date: '{date_str}'")
            return None

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str) -> None:
        if not self.webhook_url:
            logging.warning("No webhook URL configured.")
            return

        try:
            response = requests.post(self.webhook_url, json={"content": message})
            response.raise_for_status()
            logging.info("Webhook sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook: {e}")

class ForumScraper:
    MAX_PAGES = 2

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self._page_cache: Dict[str, BeautifulSoup] = {}

    def get_user_post_in_thread(self, thread_url: str, username: str) -> Optional[Post]:
        """Finds the latest post by a specific user in a thread, searching backwards."""
        current_url = self._ensure_last_page_url(thread_url)
        pages_checked = 0

        while pages_checked < self.MAX_PAGES and current_url:
            # check cache first
            if current_url in self._page_cache:
                logging.debug(f"Using cached page for {current_url}")
                soup = self._page_cache[current_url]
            else:
                logging.info(f"Checking {current_url} for user {username}...")
                try:
                    response = self.session.get(current_url, allow_redirects=True)
                    response.raise_for_status()
                    # Resolve real URL after potential redirect (action=lastpost)
                    current_url = response.url
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self._page_cache[current_url] = soup
                except requests.RequestException as e:
                    logging.error(f"Error fetching {current_url}: {e}")
                    break


            page_containers = soup.select(self.config.selectors['post_container'])
            
            # Check posts from newest to oldest
            for container in reversed(page_containers):
                post = self._parse_single_post(container)
                if post and post.username.lower() == username.lower():
                    logging.info(f"Found post for {username} on page {pages_checked + 1}.")
                    return post

            current_url = self._get_previous_page_url(soup, current_url)
            pages_checked += 1
            
        return None

    def _parse_single_post(self, container: BeautifulSoup) -> Optional[Post]:
        selectors = self.config.selectors
        try:
            user_elem = container.select_one(selectors['username'])
            date_elem = container.select_one(selectors['post_date'])

            if not user_elem or not date_elem:
                return None

            return Post(
                username=user_elem.text.strip(),
                date=DateParser.parse(date_elem.text.strip())
            )
        except Exception:
            return None

    def _ensure_last_page_url(self, url: str) -> str:
        if 'action=lastpost' not in url and 'page=' not in url:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}action=lastpost"
        return url

    def _get_previous_page_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        prev_selector = self.config.selectors.get('pagination_prev')
        if not prev_selector:
            return None
            
        prev_link = soup.select_one(prev_selector)
        if prev_link and prev_link.get('href'):
            return urljoin(base_url, prev_link.get('href'))
        return None

class ReminderBot:
    def __init__(self):
        self.config = Config(CONFIG_FILE)
        self.notifier = DiscordNotifier(self.config.webhook_url)
        self.scraper = ForumScraper(self.config)

    def run(self):
        active_players = self.config.active_players
        last_seen_dates: Dict[str, Optional[datetime]] = {}
        
        # Optimization: player-first search as requested.
        # "jeśli znajdziesz post to nie szukaj dalej tylko przejdź do kolejnego gracza"
        for player in active_players:
            logging.info(f"Searching activity for player: {player}")
            found_post = None
            
            for url in self.config.monitored_threads:
                found_post = self.scraper.get_user_post_in_thread(url, player)
                if found_post:
                    # Found the latest post for this player in one of the threads.
                    # As per "minimalna liczba stron" we stop searching other threads.
                    break
            
            last_seen_dates[player] = found_post.date if found_post else None

        self._analyze_and_notify(last_seen_dates)

    def _analyze_and_notify(self, last_seen_dates: Dict[str, Optional[datetime]]):
        today = datetime.now()
        threshold = today - timedelta(days=self.config.threshold_days)

        print("\n--- Summary ---")
        for player, last_seen in last_seen_dates.items():
            date_fmt = '%d-%m-%Y'
            
            if last_seen:
                days_inactive = (today - last_seen).days
                date_str = last_seen.strftime(date_fmt)
                
                if last_seen < threshold:
                    msg = (f"🔔 **Przypomnienie**: Gracz **{player}** nieaktywny od "
                           f"{days_inactive} dni (Ostatni post: {date_str}).")
                    print(msg)
                    self.notifier.send(msg)
                else:
                    print(f"OK: {player} (Ostatni post: {date_str}, {days_inactive} dni temu).")
            else:
                msg = (f"⚠️ **Uwaga**: Gracz **{player}** nie napisał żadnego posta "
                       "w monitorowanych wątkach (sprawdzono ostatnie strony).")
                print(msg)
                self.notifier.send(msg)

if __name__ == "__main__":
    bot = ReminderBot()
    bot.run()

