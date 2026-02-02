#!/bin/bash
set -e

echo "Starting Office-IoT server..."
docker-compose up -d

echo ""
echo "Server started on port 8878"
echo "View logs: docker-compose logs -f"
