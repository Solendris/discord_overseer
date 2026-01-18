import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from .config import Config
from .notifier import DiscordNotifier
from .scraper import ForumScraper


class ReminderBot:
    """Orchestrates the process of checking player activity and notifying via Discord."""
    def __init__(self, config: Config, notifier: DiscordNotifier, scraper: ForumScraper):
        self.config = config
        self.notifier = notifier
        self.scraper = scraper

    def run(self):
        """Executes the activity check and notification flow."""
        # Clear cache to ensure fresh data in continuous mode
        self.scraper.clear_cache()

        active_players = self.config.active_players
        last_seen_dates: Dict[str, Optional[datetime]] = {}
        
        for player in active_players:
            logging.info(f"Searching activity for player: {player}")
            found_post = None
            
            for url in self.config.monitored_threads:
                found_post = self.scraper.get_user_post_in_thread(url, player)
                if found_post:
                    break
            
            last_seen_dates[player] = found_post.date if found_post else None

        self._analyze_and_notify(last_seen_dates)

    def _analyze_and_notify(self, last_seen_dates: Dict[str, Optional[datetime]]):
        today = datetime.now()
        threshold = today - timedelta(days=self.config.threshold_days)
        
        alerts = [] # List of (message, optional_image_path)
        summary_log = []

        for player, last_seen in last_seen_dates.items():
            role_id = self.config.player_discord_role_ids.get(player)
            
            if role_id:
                clean_id = str(role_id).lstrip('&')
                player_mention = f"<@&{clean_id}>"
            else:
                player_mention = f"**{player}**"
            
            if last_seen:
                days_inactive = (today - last_seen).days
                date_str = last_seen.strftime('%d-%m-%Y')
                
                if last_seen < threshold:
                    msg = (
                        f"🔔 **Przypomnienie**: Gracz {player_mention} "
                        f"nieaktywny od {days_inactive} dni "
                        f"(Ostatni post: {date_str})."
                    )
                    
                    # Attach image only if days_inactive >= image_threshold_days
                    image_path = None
                    if days_inactive >= self.config.image_threshold_days:
                        image_path = self.config.player_images.get(player)
                        
                    alerts.append((msg, image_path))
                    summary_log.append(msg)
                else:
                    summary_log.append(f"OK: {player} (Ostatni post: {date_str}, {days_inactive} dni temu).")
            else:
                msg = (
                    f"⚠️ **Uwaga**: Gracz {player_mention} nie napisał "
                    f"żadnego posta w monitorowanych wątkach "
                    f"(sprawdzono ostatnie strony)."
                )
                # For players with NO posts, we treat them as "maximum inactivity"
                alerts.append((msg, self.config.player_images.get(player)))
                summary_log.append(msg)

        logging.info("\n--- Summary ---")
        for line in summary_log:
            logging.info(line)

        if alerts:
            overseer_msg = self.config.overseer_message
            overseer_img = self.config.overseer_image
            self.notifier.send(overseer_msg, image_path=overseer_img)
            for alert, image in alerts:
                self.notifier.send(alert, image_path=image)
