import logging
import os
import sys
import time
from src.config import Config
from src.notifier import DiscordNotifier
from src.scraper import ForumScraper
from src.bot import ReminderBot

# Global Constants
CONFIG_FILE = 'config.json'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Force UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    cfg = Config(CONFIG_FILE)
    ntf = DiscordNotifier(cfg.webhook_url)
    scrp = ForumScraper(cfg)
    
    bot = ReminderBot(config=cfg, notifier=ntf, scraper=scrp)

    # Check for Docker/Continuous environment variable
    if os.getenv('RUN_CONTINUOUSLY', 'false').lower() == 'true':
        import schedule
        interval = cfg.check_interval_minutes
        
        if interval < 1440:
            logging.info(f"Starting in continuous mode (Docker). Scheduled for run every {interval} minutes.")
            schedule.every(interval).minutes.do(bot.run)
        else:
            run_time = cfg.daily_run_time
            logging.info(f"Starting in continuous mode (Docker). Scheduled for daily run at {run_time}.")
            schedule.every().day.at(run_time).do(bot.run)

        # Run once immediately on startup
        bot.run()
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Standard run-once mode (e.g. for Windows Task Scheduler)
        bot.run()

if __name__ == "__main__":
    main()
