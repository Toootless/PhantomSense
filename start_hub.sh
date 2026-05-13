#!/bin/bash
# PhantomSense - Start Hub Server Only (WSL)

set -e

cd "$(dirname "$0")/hub"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

echo "================================================================"
echo "PhantomSense Hub Server"
echo "================================================================"
echo ""
echo "Hub is running on: http://localhost:5000"
echo "API Endpoints:"
echo "   - http://localhost:5000/devices       (list connected devices)"
echo "   - http://localhost:5000/update        (device POST data)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python hub.py
