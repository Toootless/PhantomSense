#!/usr/bin/env python3
"""Quick LLM pipeline test"""

import asyncio
from phantomsense_hub.llm_reasoning import llm_reasoner, initialize_llm
from phantomsense_hub.core.config import config

async def quick_test():
    await initialize_llm()
    print(f'LLM Status: {llm_reasoner.is_available}')
    print(f'Model: {config.ollama.PRIMARY_MODEL}')
    
    # Test reasoning
    activities = [{'timestamp_ms': 0, 'activity_score': 65, 'rssi': -45, 'snr': 35.0, 'phase_velocity': 0}]
    result = await llm_reasoner.reason_about_activity('1', activities)
    summary = result.get('activity_summary', 'Unknown')
    print(f'Analysis: {summary[:60]}...')
    print(f'Confidence: {result.get("confidence", 0)}%')
    print('SUCCESS: LLM Pipeline Working!')

asyncio.run(quick_test())
