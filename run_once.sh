#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Run the container in single-shot mode
# --rm: Remove container after exit
# -e RUN_CONTINUOUSLY=false: Override default behavior to run once
docker compose run --rm -e RUN_CONTINUOUSLY=false discord-reminder
