#!/bin/bash
# PhantomSense - Firmware Build Diagnostics
# Run this to verify your ESP-IDF setup is correct

echo "=========================================="
echo "PhantomSense Firmware Diagnostics"
echo "=========================================="
echo ""

# Check 1: Python version
echo "1️⃣  Python Version"
python3 --version || echo "✗ Python3 not found"
echo ""

# Check 2: IDF_PATH
echo "2️⃣  ESP-IDF Installation"
if [ -z "$IDF_PATH" ]; then
    echo "✗ IDF_PATH not set"
else
    echo "✓ IDF_PATH: $IDF_PATH"
    if [ -f "$IDF_PATH/export.sh" ]; then
        echo "✓ export.sh found"
    else
        echo "✗ export.sh not found"
    fi
fi
echo ""

# Check 3: idf.py
echo "3️⃣  idf.py Command"
if command -v idf.py &> /dev/null; then
    echo "✓ idf.py available"
    idf.py --version
else
    echo "✗ idf.py not in PATH"
fi
echo ""

# Check 4: ESP32-S3 Tools
echo "4️⃣  ESP32-S3 Toolchain"
if command -v xtensa-esp32s3-elf-gcc &> /dev/null; then
    echo "✓ Compiler found:"
    xtensa-esp32s3-elf-gcc --version | head -1
else
    echo "✗ Compiler not found"
fi
echo ""

# Check 5: ESPTOOL
echo "5️⃣  ESPTOOL (Flashing Tool)"
if command -v esptool.py &> /dev/null; then
    echo "✓ esptool.py available:"
    esptool.py --version
else
    echo "✗ esptool.py not found"
fi
echo ""

# Check 6: Serial Ports
echo "6️⃣  Available Serial Ports"
if [ -d "/dev" ]; then
    ports=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "none")
    if [ "$ports" != "none" ]; then
        echo "✓ Found ports:"
        echo "$ports"
    else
        echo "⚠️  No serial ports detected (board might not be connected)"
    fi
else
    echo "✗ /dev not accessible (check WSL permissions)"
fi
echo ""

# Check 7: Project Structure
echo "7️⃣  Project Structure"
if [ -f "firmware/main/main.c" ]; then
    echo "✓ firmware/main/main.c found"
else
    echo "✗ firmware/main/main.c not found"
fi

if [ -f "firmware/CMakeLists.txt" ]; then
    echo "✓ firmware/CMakeLists.txt found"
else
    echo "✗ firmware/CMakeLists.txt not found"
fi
echo ""

echo "=========================================="
echo "Diagnostics Complete"
echo "=========================================="
