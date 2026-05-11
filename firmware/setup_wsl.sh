#!/bin/bash
# PhantomSense - ESP32-S3 WSL Setup Helper
# Ensures ESP-IDF tools are properly configured in WSL environment

set -e

echo "=========================================="
echo "ESP-IDF WSL Configuration Helper"
echo "=========================================="
echo ""

# Check if ESP-IDF is installed
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  IDF_PATH not set. Searching for ESP-IDF installation..."
    
    # Common locations
    for idf_loc in ~/esp/esp-idf ~/.espressif/esp-idf /opt/esp-idf; do
        if [ -d "$idf_loc" ]; then
            echo "✓ Found ESP-IDF at: $idf_loc"
            export IDF_PATH="$idf_loc"
            break
        fi
    done
    
    if [ -z "$IDF_PATH" ]; then
        echo "✗ ESP-IDF not found. Please install via VS Code extension:"
        echo "  1. Press Ctrl+Shift+P"
        echo "  2. Type: ESP-IDF: Configure ESP-IDF Extension"
        echo "  3. Select Express Install"
        exit 1
    fi
fi

echo "✓ IDF_PATH: $IDF_PATH"

# Source the export script
if [ -f "$IDF_PATH/export.sh" ]; then
    echo "✓ Sourcing ESP-IDF environment..."
    source "$IDF_PATH/export.sh"
    echo "✓ IDF tools ready"
else
    echo "⚠️  export.sh not found at $IDF_PATH/export.sh"
fi

# Verify idf.py is available
if command -v idf.py &> /dev/null; then
    echo "✓ idf.py available:"
    idf.py --version
else
    echo "✗ idf.py not found in PATH"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. cd ~/PhantomSense/firmware"
echo "2. idf.py set-target esp32s3"
echo "3. idf.py build"
echo "4. idf.py flash -p /dev/ttyACM0"
echo ""
