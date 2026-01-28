# Discord RPG Session Reminder

> **"Because waiting for players shouldn't be a full-time job."**

## What is this?
I built this tool to automate the tedious part of running Play-by-Post RPG sessions on forums. As a Game Master, keeping track of 5 different threads and remembering who owes a reply to whom is a hassle.

This bot acts as an intelligent assistant that scans my forum threads, understands the flow of conversation, and nudges players on Discord when it's *actually* their turn.

## Why it's cool (Features)
Unlike a simple script that just pings everyone every 24 hours, this bot has **context awareness**:

*   **Smart Activity Detection**: It doesn't just check for "new posts." It compares the timestamp of the last Game Master post vs. the Player's last post.
    *   *Scenario A*: GM posted -> Player hasn't replied for 2 days -> **PING**
    *   *Scenario B*: GM posted -> Player replied -> **Silence** (Good job!)
*   **Agnostic Scraper**: It uses `BeautifulSoup` and flexible CSS selectors defined in `config.json`. It can work with MyBB, phpBB, XenForo, or any custom site just by changing the config.
*   **Dockerized**: Runs in a container, making it easy to deploy on a Raspberry Pi or a cheap VPS to run 24/7.
*   **Visual Nudges**: If a player delays too long (configurable), the bot starts attaching their character's portrait to the Discord ping to effectively urge them to post.

## Tech Stack
*   **Python 3.11+**: Core logic.
*   **BeautifulSoup4**: Robust HTML parsing.
*   **Discord Webhooks**: Lightweight notification system.

## How to Run it

### Option 1: The Docker Way (Recommended)
This method is preferred for running on a server or Raspberry Pi.

1.  Clone the repo.
2.  Rename `example_config.json` to `config.json` and fill it in (see below).
3.  Run:
    ```bash
    docker-compose up -d --build
    ```

### Option 2: The Local Way
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the bot:
    ```bash
    python main.py
    ```

---

## Configuration (`config.json`)

You need to fill in `config.json` with the details from your specific forum.

1.  **`discord_webhook_url`**: Your Discord Webhook URL.
2.  **`forum_thread_url`**: The full URL of the thread you want to scrape (e.g., `https://example.com/topic/123-game-thread/`).
3.  **`selectors`**: This is the most important part. You need to tell the bot how to find the posts, usernames, and dates on the page.

### How to find Selectors (Chrome/Firefox)
1.  Open the forum thread in your browser.
2.  Right-click on a **whole post** and select **Inspect**.
    *   Look for a class name like `<div class="post">` or `<article class="message">`.
    *   Put that in `post_container` (e.g., `.post` or `.message`).
3.  Right-click on the **Username** of a poster.
    *   Look for the class, e.g., `<a class="username">`.
    *   Put that in `username` (e.g., `.username`).
4.  Right-click on the **Date** of the post.
    *   Look for the class, e.g., `<span class="date">`.
    *   Put that in `post_date` (e.g., `.date`).

### Example Config Structure
```json
{
    "discord_webhook_url": "YOUR_WEBHOOK_URL",
    "monitored_threads": [
        "https://forum.example.com/thread-123"
    ],
    "selectors": {
        "post_container": ".post",
        "username": ".author-name",
        "post_date": ".timestamp"
    },
    "game_masters": ["GM_Name"],
    "active_players": ["Player1"]
}
```
