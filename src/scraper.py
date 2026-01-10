import logging
import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .config import Config
from .models import Post
from .utils import DateParser

class ForumScraper:
    """Scrapes forum threads to find user activity."""
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
            if current_url in self._page_cache:
                logging.debug(f"Using cached page for {current_url}")
                soup = self._page_cache[current_url]
            else:
                logging.info(f"Checking {current_url} for user {username}...")
                try:
                    response = self.session.get(current_url, allow_redirects=True)
                    response.raise_for_status()
                    current_url = response.url
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self._page_cache[current_url] = soup
                except requests.RequestException as e:
                    logging.error(f"Error fetching {current_url}: {e}")
                    break

            page_containers = soup.select(self.config.selectors['post_container'])
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
        user_elem = container.select_one(selectors['username'])
        date_elem = container.select_one(selectors['post_date'])

        if not user_elem or not date_elem:
            return None

        parsed_date = DateParser.parse(date_elem.text.strip())
        if not parsed_date:
            return None

        return Post(
            username=user_elem.text.strip(),
            date=parsed_date
        )

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
