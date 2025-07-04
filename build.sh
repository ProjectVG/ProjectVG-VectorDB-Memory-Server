#!/bin/bash
set -e

echo "[1/2] Building Docker images..."
docker-compose build

echo "[2/2] Starting containers..."
docker-compose up -d

echo "All services are up!" 