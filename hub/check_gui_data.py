#!/usr/bin/env python3
"""Check GUI data source"""
import requests
import json

resp = requests.get('http://localhost:5000/devices')
if resp.status_code == 200:
    data = resp.json()
    print('✓ Hub API Status: ONLINE')
    print(f'Units Connected: {len(data.get("units", {}))}')
    for unit_id, unit in data.get('units', {}).items():
        print(f'\n  Unit {unit_id}: {unit.get("unit_name")}')
        print(f'    Status: {"🟢 Connected" if unit.get("connected") else "🔴 Disconnected"}')
        print(f'    IP: {unit.get("ip_address")}')
        print(f'    RSSI: {unit.get("rssi")} dBm')
        activity = unit.get('latest_activity', {})
        print(f'    Activity: {activity.get("name", "Unknown")}')
        print(f'    Confidence: {activity.get("confidence", 0):.0%}')
else:
    print(f'✗ Hub API: ERROR ({resp.status_code})')
