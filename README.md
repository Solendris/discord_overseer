# Discord Reminder Bot Setup

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

### Example Config
```json
"selectors": {
    "post_container": ".message-inner",
    "username": ".message-user a.username",
    "post_date": ".message-attribution-main time"
}
```

## Running the Bot

1.  Open a terminal in this folder.
2.  Run: `python main.py`

## Automating (Daily Reference)
To run this automatically every day:
1.  Open **Task Scheduler** in Windows.
2.  Create a Basic Task -> "Daily".
3.  Action: "Start a program".
4.  Program/script: `python.exe` (use full path, e.g., `C:\Users\anaconda3\python.exe`).
5.  Add arguments: `main.py`
6.  Start in: `c:\discord_reminder`
