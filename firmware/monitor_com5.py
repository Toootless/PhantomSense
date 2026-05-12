#!/usr/bin/env python3
"""Simple serial monitor for COM5"""

import serial
import sys
import time

def main():
    PORT = 'COM5'
    BAUD = 115200
    
    try:
        print(f"Opening {PORT} at {BAUD} baud...")
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)  # Wait for device to be ready
        print(f"✓ Connected to {PORT}")
        print("=" * 70)
        print("Press Ctrl+C to exit")
        print("=" * 70 + "\n")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').rstrip()
                if line:
                    print(line)
                    
    except serial.SerialException as e:
        print(f"✗ Serial error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nMonitor closed by user")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Connection closed")

if __name__ == '__main__':
    main()
