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
            
            for url in self.config.monitored_threads:
                # Get the absolute last post in the thread
                last_post_overall = self.scraper.get_last_post_in_thread(url)
                
                # Get the last post by this specific player
                found_post = self.scraper.get_user_post_in_thread(url, player)
                
                if last_post_overall:
                    # Check if the last post was written by an excluded user (e.g., GM)
                    is_gm_post = last_post_overall.username in self.config.excluded_users
                    
                    if is_gm_post:
                        logging.info(f"Last post in thread by GM ({last_post_overall.username})")
                        
                        if found_post:
                            # Check if player's post is BEFORE GM's post
                            if found_post.date < last_post_overall.date:
                                logging.info(f"Player {player} hasn't responded to GM's post yet")
                                gm_post = last_post_overall  # Save GM's post date
                                should_check = True
                                break
                            else:
                                logging.info(f"Player {player} already responded after GM's post")
                        else:
                            # Player has no posts but GM posted - player should respond
                            logging.info(f"Player {player} has no posts, but GM is waiting for response")
                            gm_post = last_post_overall  # Save GM's post date
                            should_check = True
                            break
                    else:
                        # Last post is by a player (not GM) - no need to remind
                        logging.info(f"Last post by player ({last_post_overall.username}), no GM waiting for response")
                        if found_post:
                            break
                elif found_post:
                    # No posts in thread but player has a post (shouldn't happen, but handle it)
                    break
            
            last_seen_dates[player] = found_post.date if found_post else None
            gm_post_dates[player] = gm_post.date if gm_post else None
            should_check_player[player] = should_check

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
