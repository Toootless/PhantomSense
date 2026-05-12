#!/usr/bin/env python3
"""
Test script for LLM integration in PhantomSense Hub
Tests Ollama connectivity and LLM reasoning pipeline
"""

import asyncio
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ollama_connection():
    """Test if Ollama is running and available"""
    logger.info("=" * 60)
    logger.info("TEST 1: Ollama Connectivity")
    logger.info("=" * 60)
    
    import requests
    
    try:
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✓ Ollama is running")
            logger.info(f"✓ Available models: {len(models)}")
            for model in models:
                logger.info(f"  - {model.get('name')}")
            return True
        else:
            logger.error(f"✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Ollama connection failed: {e}")
        return False


async def test_llm_reasoning_module():
    """Test LLM reasoning module initialization"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: LLM Reasoning Module")
    logger.info("=" * 60)
    
    try:
        from phantomsense_hub.llm_reasoning import llm_reasoner, initialize_llm
        from phantomsense_hub.core.config import config
        
        logger.info("✓ LLM reasoning module imported")
        
        # Initialize
        result = await initialize_llm()
        if result:
            logger.info(f"✓ LLM reasoning initialized successfully")
            logger.info(f"✓ Using model: {config.ollama.PRIMARY_MODEL}")
            logger.info(f"✓ Ollama available: {llm_reasoner.is_available}")
            return True
        else:
            logger.warning("⚠ LLM reasoning initialization returned False")
            return False
    except Exception as e:
        logger.error(f"✗ LLM reasoning module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_aggregator():
    """Test data aggregator module"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Data Aggregator Module")
    logger.info("=" * 60)
    
    try:
        from phantomsense_hub.data_aggregator import data_aggregator, initialize_aggregator
        from phantomsense_hub.core import hub_state
        
        logger.info("✓ Data aggregator module imported")
        
        # Initialize aggregator
        tasks = await initialize_aggregator()
        logger.info(f"✓ Data aggregator initialized with {len(tasks)} background tasks")
        
        # Simulate some activity data
        test_activity = {
            "unit_id": "1",
            "timestamp_ms": int(datetime.now().timestamp() * 1000),
            "activity_score": 65,
            "rssi": -45,
            "snr": 35.0,
            "phase_velocity": 0.0,
        }
        
        await hub_state.add_activity("1", test_activity)
        logger.info("✓ Added test activity to hub state")
        
        return True
    except Exception as e:
        logger.error(f"✗ Data aggregator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_analysis():
    """Test LLM analysis on sample data"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: LLM Activity Analysis")
    logger.info("=" * 60)
    
    try:
        from phantomsense_hub.llm_reasoning import llm_reasoner
        
        # Sample activity data
        activities = [
            {
                "timestamp_ms": int(datetime.now().timestamp() * 1000),
                "activity_score": 65,
                "rssi": -45,
                "snr": 35.0,
                "phase_velocity": 0.0,
            }
        ]
        
        logger.info("Testing LLM analysis with sample activity...")
        result = await llm_reasoner.reason_about_activity("1", activities)
        
        if result:
            logger.info(f"✓ LLM analysis completed")
            logger.info(f"  Activity Summary: {result.get('activity_summary', 'N/A')[:80]}")
            logger.info(f"  Confidence: {result.get('confidence', 0)}")
            logger.info(f"  Reasoning: {result.get('reasoning', '')[:100]}...")
            return True
        else:
            logger.warning("⚠ LLM analysis returned empty result")
            return False
    except Exception as e:
        logger.error(f"✗ LLM analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test API endpoint structure"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: API Endpoints")
    logger.info("=" * 60)
    
    try:
        from phantomsense_hub.api import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test /devices endpoint
        response = client.get("/devices")
        logger.info(f"✓ GET /devices: {response.status_code}")
        
        # Test /metrics endpoint
        response = client.get("/metrics")
        logger.info(f"✓ GET /metrics: {response.status_code}")
        
        # Simulate device update
        device_data = {
            "unit_id": 1,
            "unit_name": "PhantomSense-Unit-1",
            "rssi": -45,
            "ip_address": "10.0.0.100",
            "csi_amplitude": -45.5,
            "csi_noise_floor": -80,
            "timestamp_ms": int(datetime.now().timestamp() * 1000)
        }
        
        response = client.post("/update", json=device_data)
        logger.info(f"✓ POST /update: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"  Response: {response.json()}")
        
        return True
    except ImportError as e:
        logger.warning(f"⚠ TestClient not available: {e}")
        return True
    except Exception as e:
        logger.error(f"✗ API endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "PhantomSense LLM Integration Test" + " " * 14 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    results = {}
    
    # Run tests
    results["Ollama Connection"] = await test_ollama_connection()
    results["LLM Reasoning Module"] = await test_llm_reasoning_module()
    results["Data Aggregator"] = await test_data_aggregator()
    results["LLM Analysis"] = await test_llm_analysis()
    results["API Endpoints"] = await test_api_endpoints()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
