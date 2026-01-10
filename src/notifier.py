import logging
import os
import requests
from typing import Optional

class DiscordNotifier:
    """Handles sending notifications to Discord via Webhooks."""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str, image_path: Optional[str] = None) -> None:
        """Sends a text message and optional image to a Discord Webhook."""
        if not self.webhook_url:
            logging.warning("No webhook URL configured.")
            return

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    response = requests.post(
                        self.webhook_url,
                        data={"content": message},
                        files={"file": f}
                    )
            else:
                response = requests.post(self.webhook_url, json={"content": message})
            
            response.raise_for_status()
            logging.info("Webhook sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook: {e}")
