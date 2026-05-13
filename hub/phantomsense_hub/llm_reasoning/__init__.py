"""
LLM Reasoning Engine - Uses Ollama for contextual interpretation
"""

import asyncio
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

import httpx
from ollama import AsyncClient

from ..core.config import config
from ..core import hub_state, get_logger

logger = get_logger(__name__)


class LLMReasoner:
    """LLM-based reasoning engine for activity interpretation"""
    
    def __init__(self):
        self.ollama_client = AsyncClient(base_url=config.ollama.OLLAMA_HOST)
        self.is_available = False
        self.reasoning_cache = {}
        self.context_window = []  # Activity context for reasoning
        self.max_context_size = 50  # Keep last 50 activities
    
    async def check_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            # Use httpx to check Ollama endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.ollama.OLLAMA_HOST}/api/tags",
                    timeout=5.0
                )
                self.is_available = response.status_code == 200
                
                if self.is_available:
                    logger.info(f"Ollama is available at {config.ollama.OLLAMA_HOST}")
                    # List available models
                    models = response.json().get("models", [])
                    logger.info(f"Available models: {[m.get('name') for m in models]}")
                else:
                    logger.warning("Ollama server not responding")
                
                return self.is_available
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            self.is_available = False
            return False
    
    async def reason_about_activity(self, unit_id: str, activity_history: list) -> dict:
        """Use LLM to reason about activity patterns"""
        
        if not self.is_available:
            logger.warning("Ollama not available, skipping reasoning")
            return {"reasoning": "Ollama unavailable", "confidence": 0}
        
        try:
            # Build prompt from recent activities
            prompt = self._build_activity_prompt(unit_id, activity_history)
            
            logger.debug(f"Sending reasoning request to Ollama (model: {config.ollama.PRIMARY_MODEL})")
            
            # Call Ollama with streaming
            response_text = ""
            async for chunk in await self.ollama_client.generate(
                model=config.ollama.PRIMARY_MODEL,
                prompt=prompt,
                stream=True,
                options={
                    "num_gpu": 32,  # Use all GPU layers
                    "temperature": config.ollama.TEMPERATURE,
                    "num_ctx": config.ollama.CONTEXT_WINDOW,
                }
            ):
                response_text += chunk.get("response", "")
            
            # Parse and structure response
            reasoning_result = {
                "unit_id": unit_id,
                "model": config.ollama.PRIMARY_MODEL,
                "timestamp": datetime.now().isoformat(),
                "reasoning": response_text,
                "confidence": self._extract_confidence(response_text),
                "activity_summary": self._extract_summary(response_text),
            }
            
            logger.info(f"Reasoning complete for {unit_id}: {reasoning_result['activity_summary']}")
            
            # Cache result
            self.reasoning_cache[unit_id] = reasoning_result
            
            return reasoning_result
            
        except Exception as e:
            logger.error(f"Error in LLM reasoning: {e}")
            return {
                "reasoning": f"Error: {str(e)}",
                "confidence": 0,
                "activity_summary": "Unable to reason",
            }
    
    async def analyze_patterns(self, time_window_hours: int = 1) -> dict:
        """Analyze activity patterns over time window"""
        
        if not self.is_available:
            return {"error": "Ollama unavailable"}
        
        try:
            # Collect activities from buffer in time window
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            recent_activities = [
                a for a in hub_state.activity_buffer
                if datetime.fromisoformat(a.get('timestamp', datetime.now().isoformat())) > cutoff_time
            ]
            
            if not recent_activities:
                return {"pattern": "No recent activity"}
            
            # Build pattern analysis prompt
            prompt = f"""Analyze the following activity data from the past {time_window_hours} hour(s).
            
Activities:
{json.dumps(recent_activities, indent=2)}

Provide a brief summary of patterns observed, including:
1. Overall activity level (low/moderate/high)
2. Key activity types
3. Any anomalies or concerns
4. Recommendations if any"""
            
            logger.debug("Sending pattern analysis to Ollama")
            
            response_text = ""
            async for chunk in await self.ollama_client.generate(
                model=config.ollama.PRIMARY_MODEL,
                prompt=prompt,
                stream=True,
            ):
                response_text += chunk.get("response", "")
            
            return {
                "time_window_hours": time_window_hours,
                "activity_count": len(recent_activities),
                "analysis": response_text,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {"error": str(e)}
    
    def _build_activity_prompt(self, unit_id: str, activities: list) -> str:
        """Build prompt for activity reasoning"""
        
        activities_str = json.dumps(activities[-10:], indent=2)  # Last 10 activities
        
        return f"""You are an AI assistant analyzing activity data from a WiFi-based motion detection sensor.

Unit ID: {unit_id}
Recent Activities:
{activities_str}

Based on the activity scores, phase velocities, and SNR values above, provide:
1. A brief interpretation of what the person is likely doing
2. Confidence level (0-100%)
3. Any notable patterns or concerns
4. Recommendations for further monitoring if needed

Keep response concise and actionable."""
    
    def _extract_confidence(self, response: str) -> int:
        """Extract confidence percentage from response"""
        import re
        match = re.search(r'(\d+)\s*%', response)
        if match:
            return int(match.group(1))
        return 50  # Default confidence
    
    def _extract_summary(self, response: str) -> str:
        """Extract summary from response (first line)"""
        lines = response.strip().split('\n')
        return lines[0][:100] if lines else "Unable to summarize"


# Global LLM reasoner instance
llm_reasoner = LLMReasoner()


async def initialize_llm():
    """Initialize LLM reasoning engine"""
    logger.info("Initializing LLM reasoning engine")
    
    if await llm_reasoner.check_availability():
        logger.info("LLM reasoning engine ready")
        return True
    else:
        logger.warning("LLM reasoning engine unavailable (Ollama not found)")
        return False


async def shutdown_llm():
    """Shutdown LLM reasoning engine"""
    logger.info("Shutting down LLM reasoning engine")
