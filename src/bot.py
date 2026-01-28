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
        gm_post_dates: Dict[str, Optional[datetime]] = {}  # Track when GM posted
        should_check_player: Dict[str, bool] = {}
        
        for player in active_players:
            logging.info(f"Searching activity for player: {player}")
            found_post = None
            gm_post = None
            should_check = False
            
            # Search all threads for player's most recent post (original logic)
            for url in self.config.monitored_threads:
                player_post = self.scraper.get_user_post_in_thread(url, player)
                if player_post:
                    # Found player's post in this thread
                    # Now check if GM posted AFTER this player in the SAME thread
                    last_post_in_thread = self.scraper.get_last_post_in_thread(url)
                    
                    if last_post_in_thread:
                        is_gm_post = last_post_in_thread.username in self.config.game_masters
                        
                        if is_gm_post and player_post.date < last_post_in_thread.date:
                            # GM posted after player - player needs to respond
                            logging.info(f"In thread {url}: GM ({last_post_in_thread.username}) posted after {player}")
                            found_post = player_post
                            gm_post = last_post_in_thread
                            should_check = True
                            break  # Found a thread where GM is waiting for this player
                        elif not is_gm_post or player_post.date >= last_post_in_thread.date:
                            # Player responded after GM, or last post is not GM
                            logging.info(f"In thread {url}: {player} is up to date (last: {last_post_in_thread.username})")
                            if found_post is None or player_post.date > found_post.date:
                                # Keep track of most recent player post
                                found_post = player_post
                    else:
                        # No parseable posts in thread
                        if found_post is None:
                            found_post = player_post
            
            last_seen_dates[player] = found_post.date if found_post else None
            gm_post_dates[player] = gm_post.date if gm_post else None
            should_check_player[player] = should_check
            logging.info(f"Final decision for {player}: should_check={should_check}, gm_post={'Yes' if gm_post else 'No'}")



        self._analyze_and_notify(last_seen_dates, gm_post_dates, should_check_player)

    def _analyze_and_notify(self, last_seen_dates: Dict[str, Optional[datetime]], 
                            gm_post_dates: Dict[str, Optional[datetime]],
                            should_check_player: Dict[str, bool]):
        today = datetime.now()
        threshold = today - timedelta(days=self.config.threshold_days)
        
        alerts = [] # List of (message, optional_image_path)
        summary_log = []

        for player, last_seen in last_seen_dates.items():
            # Skip if we determined that GM is not waiting for this player's response
            if not should_check_player.get(player, False):
                logging.info(f"Skipping {player} - no GM response pending")
                summary_log.append(f"OK: {player} - gracz już odpowiedział lub MG nie czeka na odpowiedź.")
                continue
            role_id = self.config.player_discord_role_ids.get(player)
            
            if role_id:
                clean_id = str(role_id).lstrip('&')
                player_mention = f"<@&{clean_id}>"
            else:
                player_mention = f"**{player}**"
            
            # Use GM post date if available, otherwise player's last seen
            gm_post_date = gm_post_dates.get(player)
            
            if gm_post_date:
                # GM is waiting for response - show how long GM has been waiting
                days_waiting = (today - gm_post_date).days
                gm_date_str = gm_post_date.strftime('%d-%m-%Y')
                
                if gm_post_date < threshold:
                    msg = (
                        f"🔔 **Przypomnienie**: Mistrz Gry czeka na odpowiedź gracza {player_mention} "
                        f"od {days_waiting} dni "
                        f"(Post MG: {gm_date_str})."
                    )
                    
                    # Attach image only if days_waiting >= image_threshold_days
                    image_path = None
                    if days_waiting >= self.config.image_threshold_days:
                        image_path = self.config.player_images.get(player)
                        
                    alerts.append((msg, image_path))
                    summary_log.append(msg)
                else:
                    summary_log.append(f"OK: {player} (MG czekał {days_waiting} dni, ale poniżej progu).")
            elif last_seen:
                # Player has posts but GM is not waiting (shouldn't reach here if logic is correct)
                days_inactive = (today - last_seen).days
                date_str = last_seen.strftime('%d-%m-%Y')
                summary_log.append(f"OK: {player} (Ostatni post: {date_str}, {days_inactive} dni temu, MG nie czeka).")
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
