#!/bin/bash

# Navigate to script directory
cd "$(dirname "$0")"

echo "Stopping all related containers..."

# Stop the main service if running
docker compose down

# Find and kill any loose containers from 'run_once'
# Filter by ancestor image name 'discord-overseer' or project name
# Note: Adjust image name if needed based on docker build
CONTAINER_IDS=$(docker ps -q --filter "ancestor=discord-overseer")

if [ -n "$CONTAINER_IDS" ]; then
    echo "Found ghost containers: $CONTAINER_IDS"
    docker stop $CONTAINER_IDS
    docker rm $CONTAINER_IDS
    echo "Ghost containers removed."
else
    echo "No ghost containers found."
fi

echo "Cleanup complete. Process logic for 'Retrospective' notifications addressed by cache clearing."
