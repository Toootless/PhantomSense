#!/bin/bash
# PhantomSense Hub - Setup Script for Franklin

set -e

echo "=============================================="
echo "PhantomSense Hub Setup (Franklin)"
echo "=============================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Setup environment
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠ Please edit .env with your configuration"
fi

# Create data directories
mkdir -p data logs

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Ensure MQTT broker is running:"
echo "   - Local: mosquitto -d"
echo "   - Remote: Update MQTT_BROKER_HOST in .env"
echo "3. Ensure Ollama is running:"
echo "   - ollama serve"
echo "4. Start the hub:"
echo "   - source venv/bin/activate"
echo "   - python hub.py"
echo ""
echo "API will be available at: http://localhost:5000"
echo "Swagger docs at: http://localhost:5000/docs"
