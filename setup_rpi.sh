#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Discord Reminder Setup for Raspberry Pi...${NC}"

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You might need to log out and back in for group changes to take effect."
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# 2. Build/Pull the image
echo "Building the Docker image..."
docker compose build

# 3. Setup Scheduler (Optional)
read -p "Do you want to setup a Cron job to run this every day at 10:00 AM? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SCRIPT_PATH="$(pwd)/run_once.sh"
    chmod +x "$SCRIPT_PATH"
    
    # Add to crontab if not exists
    # 0 10 * * * = 10:00 AM daily
    CRON_JOB="0 10 * * * $SCRIPT_PATH >> $(pwd)/cron.log 2>&1"
    
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    echo -e "${GREEN}Cron job added!${NC}"
    echo "Logs will be written to $(pwd)/cron.log"
else
    echo "Skipping Cron setup. You can run 'docker-compose up -d' to run it as a 24/7 daemon instead."
fi

echo -e "${GREEN}Setup complete!${NC}"
