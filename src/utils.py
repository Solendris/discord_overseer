import re
import logging
from datetime import datetime, timedelta
from typing import Optional

class DateParser:
    @staticmethod
    def parse(date_str: str) -> Optional[datetime]:
        now = datetime.now()
        date_str = date_str.strip().lower()

        if any(keyword in date_str for keyword in ["temu", "godzin", "minut"]):
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
            return datetime.strptime(date_str, f"%d-%m-%Y, %H:%M")
        except ValueError:
            logging.warning(f"Could not parse date: '{date_str}'")
            return None
