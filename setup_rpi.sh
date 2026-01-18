#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Discord Reminder Setup for Raspberry Pi (Daemon Mode)...${NC}"

# 1. Cleanup old mess
echo -e "${YELLOW}Cleaning up old containers and cron jobs...${NC}"
# Stop current containers
docker compose down 2>/dev/null
# Remove ghost containers
docker ps -q --filter "ancestor=discord-overseer" | xargs -r docker stop
docker ps -q --filter "ancestor=discord-overseer" | xargs -r docker rm
# Remove cron jobs containing 'discord_reminder'
crontab -l 2>/dev/null | grep -v "discord_reminder" | crontab -
echo "Cleanup complete."

# 2. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You need to log out and back in, then run this script again."
    exit 1
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# 3. Build and Run in Background
echo "Building and starting the service..."
docker compose up -d --build

echo -e "${GREEN}Setup complete! The bot is running in background.${NC}"
echo "To check logs: docker compose logs -f"
echo "To stop: docker compose down"
