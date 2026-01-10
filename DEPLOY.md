# Deploying Discord Reminder to Raspberry Pi 5

## Prerequisites
- Raspberry Pi 5 with OS installed (Raspberry Pi OS Bookworm recommended).
- SSH access to the Pi.

## Installation Steps

### 1. Transfer Files
Copy the project folder to your Raspberry Pi. You can use specific tools or `scp`:
```bash
# Run this from your computer (not the Pi)
scp -r /path/to/discord_reminder user@<rpi-ip-address>:~/discord_reminder
```

### 2. Run Setup Script
SSH into your Raspberry Pi and run the setup script. This handles Docker installation and scheduling.
```bash
ssh user@<rpi-ip-address>
cd discord_reminder
chmod +x setup_rpi.sh
./setup_rpi.sh
```

The script will ask if you want to set up a daily Cron job.
- **Answer 'y'**: If you want the bot to run once a day (saves RAM).
- **Answer 'n'**: If you want to run it manually or as a 24/7 background service.

## Manual Operation

### Daemon Mode (24/7)
If you didn't choose Cron, you can run the bot as a background service:
```bash
docker-compose up -d
```
This uses the internal scheduler (check `main.py` -> `schedule` library) to run at 10:00 AM daily.

### Single Run (Testing)
To run the bot immediately and check if it works:
```bash
chmod +x run_once.sh
./run_once.sh
```

## Troubleshooting
- **Logs (Cron)**: Check `cat cron.log` in the project directory.
- **Logs (Daemon)**: Check `docker-compose logs -f`.
- **Config**: Ensure `config.json` is correctly set up with your Webhook URL and Thread IDs.
