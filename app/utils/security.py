import secrets
import string
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

API_KEY_NAME = "X-API-SECRET"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def generate_api_secret(length: int = 32) -> str:
    """Generates a secure random API secret code. 
    Standard length is 32 characters for a balance of security and usability.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def validate_api_secret(api_key: str = Security(api_key_header)):
    """Validates the provided API secret against the configured one."""
    if not api_key or api_key != settings.API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Secret. Access denied."
        )
    return api_key

async def validate_admin_key(api_key: str = Security(api_key_header)):
    """Validates the provided Master Admin Key."""
    if not api_key or api_key != settings.MASTER_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Master Admin Key. Access denied."
        )
    return api_key
