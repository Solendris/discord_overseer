import re
import logging
from datetime import datetime, timedelta
from typing import Optional

class DateParser:
    """Utility class for parsing various Polish date formats from the forum."""
    
    @staticmethod
    def parse(date_str: str) -> Optional[datetime]:
        """
        Parses polish forum dates like:
        - "18-10-2025, 20:09"
        - "Dzisiaj, 14:30"
        - "Wczoraj, 09:12"
        - "1 godzinę temu"
        - "30 minut temu"
        """
        now = datetime.now()
        date_str = date_str.strip().lower()

        # Handle relative time "ago"
        if any(keyword in date_str for keyword in ["temu", "godzin", "minut"]):
            return now

        time_match = re.search(r'(\d{1,2}:\d{2})', date_str)
        
        # Handle "Today"
        if "dzisiaj" in date_str:
            if time_match:
                dt = datetime.strptime(time_match.group(1), "%H:%M")
                return now.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
            return now

        # Handle "Yesterday"
        if "wczoraj" in date_str:
            yesterday = now - timedelta(days=1)
            if time_match:
                dt = datetime.strptime(time_match.group(1), "%H:%M")
                return yesterday.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
            return yesterday

        # Handle standard date format
        try:
            return datetime.strptime(date_str, f"%d-%m-%Y, %H:%M")
        except ValueError:
            logging.warning(f"Could not parse date: '{date_str}'")
            return None
