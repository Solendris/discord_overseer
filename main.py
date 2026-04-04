import logging
import os
import sys
import time
from src.config import Config
from src.notifier import DiscordNotifier
from src.scraper import ForumScraper
from src.bot import ReminderBot

CONFIG_FILE = 'config.json'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    cfg = Config(CONFIG_FILE)
    ntf = DiscordNotifier(cfg.webhook_url)
    scrp = ForumScraper(cfg)
    
    bot = ReminderBot(config=cfg, notifier=ntf, scraper=scrp)

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

        bot.run()
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        bot.run()

if __name__ == "__main__":
    main()
