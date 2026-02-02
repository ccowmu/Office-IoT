#!/bin/bash
# Quick start script for Office-IoT server

echo "Building Office-IoT server..."
docker-compose build

echo "Starting Office-IoT server..."
docker-compose up -d

echo ""
echo "Server started!"
echo "Control endpoint: http://localhost:8878/control"
echo "Status endpoint: http://localhost:8877/status"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop server: docker-compose down"
