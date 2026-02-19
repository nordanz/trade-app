#!/bin/bash

# Setup script for Stock Market Dashboard

echo "📈 Stock Market Dashboard Setup"
echo "================================"
echo ""

# Check Python version (require >= 3.12)
echo "Checking Python version..."
python3 - <<'PY'
import sys
if sys.version_info < (3, 12):
    sys.stderr.write(f"Error: Python {sys.version_info.major}.{sys.version_info.minor} detected. Python 3.12 or newer is required.\n")
    sys.exit(2)
print("Python " + sys.version.split()[0] + " detected.")
PY
if [ $? -ne 0 ]; then
    echo "Please install Python 3.12+ and ensure 'python3' points to it."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing all dependencies..."
pip install -e '.[dev,news]'

# Copy environment file
echo ""
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
else
    echo ".env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Gemini API key"
echo "   Get one at: https://makersuite.google.com/app/apikey"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the dashboard:"
echo "   streamlit run dashboard/app.py"
echo ""
echo "4. Or run tests:"
echo "   python tests/test_services.py"
echo ""
