import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List

from .config import Config
from .notifier import DiscordNotifier
from .scraper import ForumScraper, Post


class ReminderBot:    
    def __init__(self, config: Config, notifier: DiscordNotifier, scraper: ForumScraper):
        self.config = config
        self.notifier = notifier
        self.scraper = scraper

    def run(self):
        try:
            self.scraper.clear_cache()

            player_statuses = self._check_all_players()
            self._analyze_and_notify(player_statuses)
        finally:
            self.scraper.clear_cache()

    def _check_all_players(self) -> Dict[str, Dict]:
        player_statuses = {}
        
        for player in self.config.active_players:
            logging.info(f"Searching activity for player: {player}")
            status = self._check_player_status(player)
            player_statuses[player] = status
            
            logging.info(
                f"Final decision for {player}: should_check={status['should_check']}, "
                f"gm_post={'Yes' if status['gm_post_date'] else 'No'}"
            )
        
        return player_statuses

    def _check_player_status(self, player: str) -> Dict:
        found_post = None
        gm_post = None
        should_check = False
        
        for url in self.config.monitored_threads:
            player_post = self.scraper.get_user_post_in_thread(url, player)
            if not player_post:
                continue
            
            last_post = self.scraper.get_last_post_in_thread(url)
            
            if self._is_gm_waiting_for_player(player, player_post, last_post, url):
                found_post = player_post
                gm_post = last_post
                should_check = True
                break
            else:
                found_post = self._keep_most_recent(found_post, player_post)
        
        return {
            'last_seen': found_post.date if found_post else None,
            'gm_post_date': gm_post.date if gm_post else None,
            'should_check': should_check
        }

    def _is_gm_waiting_for_player(self, player: str, player_post: Post, 
                                   last_post: Optional[Post], url: str) -> bool:
        if not last_post:
            return False
        
        is_gm = last_post.username in self.config.game_masters
        gm_waiting = is_gm and player_post.date < last_post.date
        
        if gm_waiting:
            logging.info(f"In thread {url}: GM ({last_post.username}) posted after {player}")
        else:
            logging.info(f"In thread {url}: {player} is up to date (last: {last_post.username})")
        
        return gm_waiting

    def _keep_most_recent(self, current: Optional[Post], new: Post) -> Post:
        if current is None or new.date > current.date:
            return new
        return current

    def _analyze_and_notify(self, player_statuses: Dict[str, Dict]):
        today = datetime.now()
        threshold = today - timedelta(days=self.config.threshold_days)
        
        alerts = []
        summary_log = []

        for player, status in player_statuses.items():
            if not status['should_check']:
                logging.info(f"Skipping {player} - no GM response pending")
                summary_log.append(f"OK: {player} - gracz już odpowiedział lub MG nie czeka na odpowiedź.")
                continue
            
            alert_data = self._process_player_alert(player, status, today, threshold)
            
            if alert_data['alert']:
                alerts.append((alert_data['message'], alert_data['image']))
                summary_log.append(alert_data['message'])
            elif alert_data['summary']:
                summary_log.append(alert_data['summary'])

        self._log_summary(summary_log)
        self._send_alerts(alerts)

    def _process_player_alert(self, player: str, status: Dict, 
                              today: datetime, threshold: datetime) -> Dict:
        player_mention = self._get_player_mention(player)
        gm_post_date = status['gm_post_date']
        last_seen = status['last_seen']
        
        if gm_post_date.date() and gm_post_date.date() <= threshold.date():
            msg, img = self._build_gm_waiting_alert(player, player_mention, gm_post_date, today)
            return {'alert': True, 'message': msg, 'image': img, 'summary': None}
        
        elif gm_post_date:
            days_waiting = (today.date() - gm_post_date.date()).days
            return {
                'alert': False, 
                'message': None, 
                'image': None,
                'summary': f"OK: {player} (MG czekał {days_waiting} dni, ale poniżej progu)."
            }
        
        elif last_seen:
            days_inactive = (today.date() - last_seen.date()).days
            date_str = last_seen.strftime('%d-%m-%Y')
            return {
                'alert': False,
                'message': None,
                'image': None,
                'summary': f"OK: {player} (Ostatni post: {date_str}, {days_inactive} dni temu, MG nie czeka)."
            }
        
        else:
            msg = self._build_no_posts_alert(player_mention)
            img = self.config.player_images.get(player)
            return {'alert': True, 'message': msg, 'image': img, 'summary': None}

    def _get_player_mention(self, player: str) -> str:
        role_id = self.config.player_discord_role_ids.get(player)
        if role_id:
            clean_id = str(role_id).lstrip('&')
            return f"<@&{clean_id}>"
        return f"**{player}**"

    def _build_gm_waiting_alert(self, player: str, player_mention: str, 
                                gm_post_date: datetime, today: datetime) -> Tuple[str, Optional[str]]:
        days_waiting = (today.date() - gm_post_date.date()).days
        gm_date_str = gm_post_date.strftime('%d-%m-%Y')
        
        msg = (
            f"🔔 **Przypomnienie**: Mistrz Gry czeka na odpowiedź gracza {player_mention} "
            f"od {days_waiting} dni (Post MG: {gm_date_str})."
        )
        
        image_path = None
        if days_waiting >= self.config.image_threshold_days:
            image_path = self.config.player_images.get(player)
        
        return msg, image_path

    def _build_no_posts_alert(self, player_mention: str) -> str:
        return (
            f"⚠️ **Uwaga**: Gracz {player_mention} nie napisał "
            f"żadnego posta w monitorowanych wątkach "
            f"(sprawdzono ostatnie strony)."
        )

    def _log_summary(self, summary_log: List[str]):
        logging.info("\n--- Summary ---")
        for line in summary_log:
            logging.info(line)

    def _send_alerts(self, alerts: List[Tuple[str, Optional[str]]]):
        """Send Discord notifications for all alerts.
        
        Args:
            alerts: List of (message, image_path) tuples
        """
        if not alerts:
            return
        
        self.notifier.send(
            self.config.overseer_message, 
            image_path=self.config.overseer_image
        )
        
        for alert_msg, image_path in alerts:
            self.notifier.send(alert_msg, image_path=image_path)
