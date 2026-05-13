#!/bin/bash
# PhantomSense - Start Hub + GUI in WSL
# This script launches both services in background processes

set -e

echo "================================================================"
echo "PhantomSense - Starting Hub + GUI (WSL)"
echo "================================================================"
echo ""

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "hub/venv" ]; then
    echo "Creating virtual environment..."
    cd hub
    python3 -m venv venv
    cd ..
fi

# Activate venv
echo "Activating virtual environment..."
source hub/venv/bin/activate

# Start Hub in background
echo ""
echo "================================================================"
echo "Starting Hub Server on http://localhost:5000"
echo "================================================================"
cd hub
python hub.py &
HUB_PID=$!
echo "Hub running (PID: $HUB_PID)"

# Give hub time to start
sleep 3

# Start Desktop GUI in background
echo ""
echo "================================================================"
echo "Starting Desktop GUI Application"
echo "================================================================"
python launch_desktop.py &
GUI_PID=$!
echo "GUI running (PID: $GUI_PID)"

echo ""
echo "================================================================"
echo "System Started!"
echo "================================================================"
echo ""
echo "Hub Server:        http://localhost:5000"
echo "GUI:               Running"
echo ""
echo "Hub PID:           $HUB_PID"
echo "GUI PID:           $GUI_PID"
echo ""
echo "To stop, press Ctrl+C or run:"
echo "  kill $HUB_PID $GUI_PID"
echo ""

# Wait for processes
wait
