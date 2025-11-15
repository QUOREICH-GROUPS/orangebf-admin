#!/bin/bash
# Usage: ./deploy.sh pi@192.168.1.20 /home/pi/orangebf
# Requires SSH access with key auth.

set -euo pipefail

TARGET_HOST=${1:-"pi@raspberrypi.local"}
TARGET_DIR=${2:-"/home/pi/orangebf"}

echo "Building frontend (admin-robot-ui)..."
pushd admin-robot-ui > /dev/null
npm install
npm run build
popd > /dev/null

echo "Syncing repository to ${TARGET_HOST}:${TARGET_DIR}..."
rsync -av --delete \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude 'admin-robot-ui/node_modules' \
    --exclude 'admin-robot-ui/dist' \
    ./ "${TARGET_HOST}:${TARGET_DIR}/"

echo "Copying frontend dist/..."
rsync -av admin-robot-ui/dist/ "${TARGET_HOST}:${TARGET_DIR}/ui/dist/"

echo "Restarting backend service..."
ssh "${TARGET_HOST}" "cd ${TARGET_DIR} && sudo systemctl restart orange.service"

echo "Deployment complete."
