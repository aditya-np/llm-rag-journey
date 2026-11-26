import hashlib
import hmac

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


def current_customer_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token required")
    token_digest = hashlib.sha256(credentials.credentials.encode()).digest()
    matched_customer = None
    for configured_token, customer_id in settings.demo_tokens.items():
        match = hmac.compare_digest(token_digest, hashlib.sha256(configured_token.encode()).digest())
        if match:
            matched_customer = customer_id
    if matched_customer is not None:
        return matched_customer
    raise HTTPException(status_code=401, detail="Invalid bearer token")

