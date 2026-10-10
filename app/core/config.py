import os
import logging
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bridge-api")

load_dotenv()

class Settings(BaseSettings):
    # The Master Key is used ONLY to generate new API secrets
    MASTER_ADMIN_KEY: str = os.getenv("MASTER_ADMIN_KEY", "")
    API_SECRET: str = os.getenv("API_SECRET", "")
    GHCR_IMAGE: str = os.getenv("GHCR_IMAGE", "")
    ENGINE_PORT: int = int(os.getenv("ENGINE_PORT", 8000))
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", 8080))
    
    # Path to store predefined files for the engine
    # Use a generic path to avoid user-specific names
    FILES_STORAGE_PATH: str = os.getenv("FILES_STORAGE_PATH", "/opt/bridge-api/storage")

settings = Settings()
