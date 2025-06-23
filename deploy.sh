#!/bin/bash

APP_DIR="/home/fincofella/app"
VENV_DIR="$APP_DIR/.venv"

echo "📁 Navigating to project directory..."
cd $APP_DIR

echo "🐍 Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Restarting Flask app..."

# Kill previous process (if running)
pkill -f "python3 app.py"

# Start app in background
nohup python3 app.py > flask.log 2>&1 &

echo "✅ Deployment complete."
