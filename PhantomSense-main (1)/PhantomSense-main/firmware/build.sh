#!/bin/bash
# PhantomSense Firmware Build Script
# Supports building and flashing for multiple units

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
UNIT_ID=${UNIT_ID:-1}
ACTION=${ACTION:-build}  # build, flash, monitor, fullbuild
PORT=${PORT:-}

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

usage() {
    cat << EOF
PhantomSense Firmware Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    -u, --unit UNIT_ID      Unit ID to build for (1 or 2, default: 1)
    -a, --action ACTION     Action: build, flash, monitor, fullbuild (default: build)
    -p, --port PORT         Serial port for flashing (default: auto-detect)
    -h, --help              Show this help message

EXAMPLES:
    # Build for Unit 1
    $0 -u 1

    # Build and flash for Unit 2
    $0 -u 2 -a fullbuild

    # Monitor serial output
    $0 -u 1 -a monitor

    # Flash with specific port
    $0 -u 1 -a flash -p /dev/ttyUSB0
EOF
}

# Parse arguments
while [[ \$# -gt 0 ]]; do
    case \$1 in
        -u|--unit)
            UNIT_ID=\$2
            shift 2
            ;;
        -a|--action)
            ACTION=\$2
            shift 2
            ;;
        -p|--port)
            PORT=\$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: \$1"
            usage
            exit 1
            ;;
    esac
done

# Validate unit ID
if [[ \$UNIT_ID != "1" && \$UNIT_ID != "2" ]]; then
    print_error "Invalid unit ID: \$UNIT_ID (must be 1 or 2)"
    exit 1
fi

# Set IDF target
print_header "Configuring for Unit \$UNIT_ID"

# Update unit selection in header file
UNIT_MACRO="UNIT_ID_\$UNIT_ID"
sed -i "s/#define CURRENT_UNIT_ID.*/#define CURRENT_UNIT_ID \$UNIT_MACRO/" main/include/app_config.h
print_info "Set CURRENT_UNIT_ID to \$UNIT_MACRO"

# Set target
print_info "Setting IDF target to esp32s3"
idf.py set-target esp32s3

# Handle actions
case \$ACTION in
    build)
        print_header "Building firmware for Unit \$UNIT_ID"
        idf.py build
        ;;
    
    fullbuild)
        print_header "Full rebuild and flash for Unit \$UNIT_ID"
        idf.py fullclean
        idf.py build
        if [ -z "\$PORT" ]; then
            idf.py flash
        else
            idf.py -p \$PORT flash
        fi
        ;;
    
    flash)
        print_header "Flashing firmware for Unit \$UNIT_ID"
        if [ -z "\$PORT" ]; then
            idf.py flash
        else
            idf.py -p \$PORT flash
        fi
        ;;
    
    monitor)
        print_header "Monitoring Unit \$UNIT_ID"
        if [ -z "\$PORT" ]; then
            idf.py monitor
        else
            idf.py -p \$PORT monitor
        fi
        ;;
    
    *)
        print_error "Unknown action: \$ACTION"
        usage
        exit 1
        ;;
esac

print_header "Done!"
