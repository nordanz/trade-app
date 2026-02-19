#!/bin/bash

# Run the eSignal Dashboard (Dash)

echo "🚀 Starting eSignal Dashboard..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your GEMINI_API_KEY"
    echo "Get your key at: https://makersuite.google.com/app/apikey"
    echo ""
fi

# Run the Dash app
echo "Starting Dash dashboard on http://localhost:8050 ..."
python dashboard/app.py

echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""
