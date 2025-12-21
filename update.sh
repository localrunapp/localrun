#!/bin/bash

# LocalRun Update Script
# This script uses Watchtower to update the running containers.
# It works for both docker-compose and docker run setups.

set -e

echo "Starting LocalRun update via Watchtower..."

# Run Watchtower to update containers
# We target specific container names if known, or let it update all if not.
# Assuming standard names 'localrun-backend' and 'portal-frontend' based on previous context.
# If you renamed your containers, please adjust the names below.

docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    containrrr/watchtower \
    --run-once \
    --cleanup \
    localrun-backend portal-frontend

echo "Watchtower update initiated. Containers should be restarting..."
