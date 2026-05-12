#!/usr/bin/env python3
import requests
import json

try:
    resp = requests.get('http://localhost:5000/api/devices', timeout=5)
    data = resp.json()
    
    print("=" * 70)
    print("HUB DEVICE STATUS")
    print("=" * 70)
    
    for unit_id, unit_data in data.get('units', {}).items():
        print(f"\nUnit: {unit_id} ({unit_data.get('unit_name')})")
        print(f"  Connected: {unit_data.get('connected')}")
        print(f"  IP: {unit_data.get('ip_address')}")
        print(f"  RSSI: {unit_data.get('rssi')} dBm")
        print(f"  Frames: {unit_data.get('frame_count')}")
    
    print(f"\nTotal Frames: {data.get('total_frames')}")
    print(f"Total Activities: {data.get('total_activities')}")
    print("=" * 70)
except Exception as e:
    print(f"Error: {e}")
