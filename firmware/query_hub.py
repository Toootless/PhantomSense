#!/usr/bin/env python3
import requests
import json

resp = requests.get('http://localhost:5000/devices', timeout=5)
data = resp.json()

print("=" * 70)
print("HUB DEVICE STATUS")
print("=" * 70)

if 'units' in data:
    for unit_id, unit_data in data['units'].items():
        connected = "✓ CONNECTED" if unit_data.get('connected') else "✗ DISCONNECTED"
        print(f"\nUnit {unit_id}: {unit_data.get('unit_name')}")
        print(f"  Status: {connected}")
        print(f"  IP: {unit_data.get('ip_address')}")
        print(f"  RSSI: {unit_data.get('rssi')} dBm")
        print(f"  Frames: {unit_data.get('frame_count')}")
else:
    print("No units in response")
    print(json.dumps(data, indent=2))

print(f"\nTotal Frames: {data.get('total_frames')}")
print(f"Total Activities: {data.get('total_activities')}")
print("=" * 70)
