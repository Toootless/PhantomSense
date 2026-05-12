"""
LLM Reasoning Module for PhantomSense
Uses Ollama to perform activity analysis on aggregated CSI data
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5-coder:1.5b-base"  # Fast model for edge cases
OLLAMA_TIMEOUT = 30  # seconds


class LLMReasoning:
    """LLM-based activity reasoning and analysis"""
    
    def __init__(self):
        self.available = False
        self.model = OLLAMA_MODEL
        self.last_error = None
        
    async def initialize(self) -> bool:
        """Initialize LLM connection and verify model availability"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.warning("Ollama API returned non-200 status")
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if self.model not in model_names:
                # Try to use another available model
                if model_names:
                    self.model = model_names[0]
                    logger.info(f"Model {OLLAMA_MODEL} not available, using {self.model}")
                else:
                    logger.warning("No models available in Ollama")
                    return False
            
            self.available = True
            logger.info(f"LLM reasoning initialized with model: {self.model}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to initialize LLM: {e}")
            return False
    
    async def analyze_csi_pattern(self, csi_data: Dict[str, Any], 
                                   unit_id: str, unit_name: str) -> Dict[str, Any]:
        """
        Analyze CSI data pattern and classify likely activity
        
        Args:
            csi_data: Dict with amplitude_mean, noise_floor, timestamp
            unit_id: Device unit ID
            unit_name: Device unit name
            
        Returns:
            Dict with activity_name, confidence, reasoning
        """
        
        if not self.available:
            return {
                "activity": "Unknown",
                "confidence": 0.0,
                "reasoning": "LLM not available"
            }
        
        try:
            # Build analysis prompt
            amplitude = csi_data.get("amplitude_mean", 0)
            noise_floor = csi_data.get("noise_floor", -80)
            
            prompt = f"""
Analyze this WiFi CSI (Channel State Information) sensor reading and classify the likely activity:

Device: {unit_name}
CSI Amplitude Mean: {amplitude:.2f}
Noise Floor: {noise_floor} dBm

Based on WiFi channel state information, classify the most likely user activity. 
Consider that:
- Stable patterns suggest stationary activity
- Fluctuating patterns suggest movement
- High amplitude suggests proximity
- Low amplitude suggests distance or obstacles

Respond in JSON format:
{{
    "activity": "activity_name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}
"""
            
            # Call Ollama
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"Ollama returned {response.status_code}")
                return self._default_analysis(amplitude, noise_floor)
            
            result_text = response.json().get("response", "")
            
            # Extract JSON from response
            try:
                # Find JSON in response
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return {
                        "activity": analysis.get("activity", "Unknown"),
                        "confidence": min(1.0, max(0.0, analysis.get("confidence", 0.5))),
                        "reasoning": analysis.get("reasoning", result_text[:100])
                    }
            except (json.JSONDecodeError, AttributeError):
                pass
            
            # Fallback to default analysis
            return self._default_analysis(amplitude, noise_floor)
            
        except requests.exceptions.Timeout:
            logger.warning(f"Ollama request timed out ({OLLAMA_TIMEOUT}s)")
            return self._default_analysis(amplitude, noise_floor)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._default_analysis(amplitude, noise_floor)
    
    def _default_analysis(self, amplitude: float, noise_floor: int) -> Dict[str, Any]:
        """Fallback heuristic analysis when LLM unavailable"""
        
        # Simple heuristic analysis
        snr = amplitude - noise_floor if amplitude > noise_floor else 0
        
        if snr > 10:
            activity = "Near Activity"
            confidence = 0.7
        elif snr > 0:
            activity = "General Activity"
            confidence = 0.6
        else:
            activity = "Far Activity"
            confidence = 0.4
        
        return {
            "activity": activity,
            "confidence": confidence,
            "reasoning": f"SNR-based heuristic (SNR={snr:.1f}dB)"
        }
    
    async def batch_analyze(self, data_batch: list) -> list:
        """Analyze multiple data points efficiently"""
        tasks = []
        for item in data_batch:
            task = self.analyze_csi_pattern(
                item.get("csi_data", {}),
                item.get("unit_id", "unknown"),
                item.get("unit_name", "Unknown Device")
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)


# Global LLM instance
llm_reasoning = LLMReasoning()


async def initialize_llm() -> bool:
    """Initialize LLM reasoning module"""
    return await llm_reasoning.initialize()


async def shutdown_llm():
    """Shutdown LLM (cleanup if needed)"""
    logger.info("LLM reasoning module shutdown")
