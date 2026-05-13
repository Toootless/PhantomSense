#!/usr/bin/env python3
"""
Test Data Generator for PhantomSense GUI Testing
Generates mock CSI and activity data without requiring MQTT or ESP32 hardware
"""

import json
import time
import random
import requests
from datetime import datetime
from statistics import mean

# Hub API endpoint
HUB_URL = "http://localhost:5000"

def generate_csi_frame():
    """Generate realistic mock CSI data (48 subcarriers for 802.11n HT20)"""
    # Simulate a walking activity with varying CSI amplitudes
    base_amp = random.uniform(20, 40)
    noise = [random.uniform(5, 15) for _ in range(48)]
    signal = [base_amp + random.gauss(0, 3) for _ in range(48)]
    return signal

def generate_activity_data():
    """Generate activity classification result"""
    activities = [
        ("walking", 0.85),
        ("standing", 0.78),
        ("sitting", 0.82),
        ("idle", 0.90),
    ]
    activity, confidence = random.choice(activities)
    # Add variance
    confidence += random.gauss(0, 0.05)
    confidence = max(0.7, min(1.0, confidence))
    return activity, confidence

def generate_mock_device_data():
    """Generate complete mock data for one device"""
    csi_frame = generate_csi_frame()
    activity, confidence = generate_activity_data()
    
    return {
        "csi_amplitude": csi_frame,
        "csi_mean": mean(csi_frame),
        "noise_floor": random.uniform(5, 15),
        "snr": random.uniform(20, 40),
        "activity": activity,
        "confidence": confidence,
        "timestamp": time.time(),
    }

def log_data(unit_id, data):
    """Log generated data to console"""
    print(f"  {unit_id:12} | Activity: {data['activity']:8} | Confidence: {data['confidence']:.2%} | SNR: {data['snr']:.1f}dB")

def generate_continuous(duration_seconds=300, interval=1):
    """Generate test data continuously
    
    Args:
        duration_seconds: How long to generate data
        interval: Seconds between updates
    """
    print("\n" + "=" * 70)
    print("🚀 PhantomSense Test Data Generator")
    print("=" * 70)
    print(f"Duration: {duration_seconds}s | Interval: {interval}s")
    print(f"Hub API: {HUB_URL}/api/devices")
    print("-" * 70)
    print("Unit ID      | Activity | Confidence | SNR")
    print("-" * 70)
    
    start_time = time.time()
    data_count = 0
    units = ["ESP32-01", "ESP32-02"]
    
    try:
        while time.time() - start_time < duration_seconds:
            # Generate data for each unit
            for unit_id in units:
                data = generate_mock_device_data()
                log_data(unit_id, data)
                data_count += 1
            
            elapsed = time.time() - start_time
            remaining = duration_seconds - elapsed
            print(f"\n⏱️  Elapsed: {elapsed:6.1f}s | Remaining: {remaining:6.1f}s | Generated: {data_count} frames")
            print("-" * 70)
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("=" * 70)
    print(f"✅ Generator finished")
    print(f"Total data frames generated: {data_count}")
    print("\n📊 Next steps:")
    print("  1. Check the GUI for activity updates")
    print("  2. Verify CSI graphs are rendering")
    print("  3. Check LLM confidence scores")
    print("\nTo use real ESP32 units:")
    print("  • Configure ESP32 units with MQTT broker IP")
    print("  • Start Mosquitto MQTT broker")
    print("  • ESP32 units will auto-connect and send CSI data")
    print("=" * 70)

if __name__ == "__main__":
    # Generate test data for 5 minutes at 1 Hz (one update per second for all units)
    generate_continuous(duration_seconds=300, interval=1)
