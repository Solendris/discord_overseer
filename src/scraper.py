import logging
import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .config import Config
from .models import Post
from .utils import DateParser


class ForumScraper:
    MAX_PAGES = 2

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self._page_cache: Dict[str, BeautifulSoup] = {}

    def clear_cache(self):
        self._page_cache.clear()
        self.session.close()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})

    def get_user_post_in_thread(self, thread_url: str, username: str) -> Optional[Post]:
        current_url = self._ensure_last_page_url(thread_url)
        pages_checked = 0

        while pages_checked < self.MAX_PAGES and current_url:
            soup = self._fetch_page(current_url, username)
            if not soup:
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

    def get_last_post_in_thread(self, thread_url: str) -> Optional[Post]:
        current_url = self._ensure_last_page_url(thread_url)
        soup = self._fetch_page(current_url, "last post")
        
        if not soup:
            return None
        
        page_containers = soup.select(self.config.selectors['post_container'])
        logging.info(f"Found {len(page_containers)} posts on last page")
        
        for container in reversed(page_containers):
            post = self._parse_single_post(container)
            if post:
                logging.info(f"Last post in thread by: {post.username} on {post.date.strftime('%d-%m-%Y')}")
                return post
        
        logging.warning(f"Could not parse any posts on last page - check selectors")
        return None

    def _fetch_page(self, url: str, context: str = "") -> Optional[BeautifulSoup]:
        if url in self._page_cache:
            logging.debug(f"Using cached page for {url}")
            return self._page_cache[url]
        
        log_msg = f"Fetching {url}"
        if context:
            log_msg += f" for {context}"
        logging.info(log_msg + "...")
        
        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            actual_url = response.url
            soup = BeautifulSoup(response.text, 'html.parser')
            self._page_cache[actual_url] = soup
            return soup
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def _parse_single_post(self, container: BeautifulSoup) -> Optional[Post]:
        selectors = self.config.selectors
        user_elem = container.select_one(selectors['username'])
        date_elem = container.select_one(selectors['post_date'])

        if not user_elem:
            logging.debug(f"Could not find username with selector: {selectors['username']}")
            return None
        if not date_elem:
            logging.debug(f"Could not find date with selector: {selectors['post_date']}")
            return None

        parsed_date = DateParser.parse(date_elem.text.strip())
        if not parsed_date:
            logging.debug(f"Could not parse date: '{date_elem.text.strip()}'")
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
