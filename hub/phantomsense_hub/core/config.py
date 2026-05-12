"""
PhantomSense Hub Configuration
Optimized for Franklin workstation (Ryzen 9, 96GB RAM, dual GPU)
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class FranklinConfig(BaseSettings):
    """Hardware-specific configuration for Franklin"""
    
    # CPU Configuration
    CPU_CORES: int = 8  # Ryzen 9 8945HS has 8 cores
    CPU_THREADS: int = 16  # With hyperthreading
    
    # Memory Configuration
    RAM_GB: int = 96
    RESERVED_RAM_GB: int = 20  # Reserve 20GB for system
    AVAILABLE_RAM_GB: int = RAM_GB - RESERVED_RAM_GB
    
    # GPU Configuration
    USE_GPU: bool = True
    GPU_DEVICES: list = ["cuda:0", "rocm:0"]  # RTX 3060 (NVIDIA), RX 7900 XTX (AMD)
    PRIMARY_GPU: str = "cuda:0"  # NVIDIA RTX 3060 as primary
    SECONDARY_GPU: str = "rocm:0"  # AMD RX 7900 XTX as secondary
    
    # GPU Memory
    PRIMARY_GPU_VRAM_GB: int = 12  # RTX 3060
    SECONDARY_GPU_VRAM_GB: int = 24  # RX 7900 XTX
    
    # Threading & Async
    WORKER_THREADS: int = 8
    ASYNC_QUEUE_SIZE: int = 1024


class MQTTConfig(BaseSettings):
    """MQTT Broker Configuration"""
    
    BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    USERNAME: str = os.getenv("MQTT_USERNAME", "phantomsense")
    PASSWORD: str = os.getenv("MQTT_PASSWORD", "phantom_pass")
    
    # Topic configuration
    TOPIC_PREFIX: str = "/phantomsense"
    TOPIC_CSI_DATA: str = f"{TOPIC_PREFIX}/+/csi_data"
    TOPIC_ACTIVITY: str = f"{TOPIC_PREFIX}/+/activity"
    TOPIC_STATUS: str = f"{TOPIC_PREFIX}/+/status"
    TOPIC_INFERENCE: str = f"{TOPIC_PREFIX}/inference"
    TOPIC_REASONING: str = f"{TOPIC_PREFIX}/reasoning"
    
    # Connection settings
    KEEPALIVE: int = 60
    RECONNECT_DELAY: int = 5
    MAX_RECONNECT_ATTEMPTS: int = 10
    
    # Quality of Service
    QOS: int = 1  # At least once delivery


class OllamaConfig(BaseSettings):
    """Ollama LLM Configuration"""
    
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Model configuration
    PRIMARY_MODEL: str = "llama3.1:8b"  # Using llama3.1 which is available
    SECONDARY_MODEL: str = "qwen2.5-coder:1.5b-base"  # Alternative fast model
    
    # GPU allocation
    GPU_LAYERS: int = 32  # Full GPU acceleration
    CONTEXT_WINDOW: int = 4096
    
    # Request parameters
    REQUEST_TIMEOUT: int = 120  # 2 minutes
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.7


class APIConfig(BaseSettings):
    """REST API Configuration"""
    
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: list = ["*"]
    ALLOW_CREDENTIALS: bool = True
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # Per second


class DatabaseConfig(BaseSettings):
    """Database Configuration"""
    
    # SQLite for local data
    DB_PATH: Path = PROJECT_ROOT / "hub" / "data" / "phantomsense.db"
    DB_URL: str = f"sqlite:///{DB_PATH}"
    
    # Retention policies
    DATA_RETENTION_DAYS: int = 30
    CLEANUP_INTERVAL_HOURS: int = 24


class HubConfig(BaseSettings):
    """Main Hub Configuration"""
    
    # Components
    franklin: FranklinConfig = FranklinConfig()
    mqtt: MQTTConfig = MQTTConfig()
    ollama: OllamaConfig = OllamaConfig()
    api: APIConfig = APIConfig()
    database: DatabaseConfig = DatabaseConfig()
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = PROJECT_ROOT / "hub" / "logs" / "hub.log"
    
    # Hub settings
    MAX_UNITS: int = 10
    BUFFER_SIZE: int = 10000
    AGGREGATION_INTERVAL_MS: int = 100  # Process data every 100ms
    
    class Config:
        env_file = PROJECT_ROOT / "hub" / ".env"
        case_sensitive = False


# Global configuration instance
config = HubConfig()
