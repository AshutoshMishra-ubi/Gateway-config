import os
import time
from typing import Optional
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

router = APIRouter(tags=["Local OIDC Token Generator"])

# Load permanent private key from disk
KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "keys", "private_key.pem")
with open(KEY_PATH, "rb") as f:
    PRIVATE_KEY = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

KEY_ID = "gateway-permanent-key-1"
GITHUB_PAGES_ISSUER = "https://ashutoshmishra-ubi.github.io/Gateway-config"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    claims: dict

@router.post("/auth/token", response_model=TokenResponse)
def generate_token(
    department: str = Query(default="finance", description="Department claim, e.g. finance, engineering, hr"),
    sub: str = Query(default="user-123", description="Subject / User ID"),
    role: str = Query(default="analyst", description="Role claim"),
    audience: str = Query(default="local-test-client", description="Audience (must match gateway allowedAudience)")
):
    now = int(time.time())
    expires_in = 3600
    
    payload = {
        "iss": GITHUB_PAGES_ISSUER,
        "sub": sub,
        "aud": audience,
        "iat": now,
        "exp": now + expires_in,
        "department": department,
        "role": role
    }
    
    pem = PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    token = jwt.encode(
        payload,
        pem,
        algorithm="RS256",
        headers={"kid": KEY_ID}
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        claims=payload
    )
