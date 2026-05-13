#!/bin/bash
# PhantomSense - Start Desktop GUI Only (WSL)

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
echo "PhantomSense Desktop GUI"
echo "================================================================"
echo ""
echo "Launching PyQt6 application..."
echo "Make sure the Hub Server is running first (use start_hub.sh)"
echo ""

python launch_desktop.py
