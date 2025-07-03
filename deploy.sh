#!/bin/bash

APP_DIR="/home/fincofella/app"
VENV_DIR="$APP_DIR/.venv"

echo "📁 Navigating to project directory..."
cd $APP_DIR

echo "🐍 Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀  Restarting Gunicorn via systemd..."
sudo systemctl restart fincofella.service

echo "✅ Deployment complete."
