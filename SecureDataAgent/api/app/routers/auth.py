import os
import time
from typing import Optional
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

router = APIRouter(tags=["Local OIDC Token Generator"])

# Default PEM matching the Netlify jwks.json
DEFAULT_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCw/61edHM7RMCz
Oq6E9F1PtyOtFpv96XdmdLBcYn6C7cRtw/fd3M+yF6v4OqEo3QZdG7Ku5u5FAEW5
C26jry6IEr4VuDyd606QnRQrvH1jRtnF3NE90rJBlGqrX3OBYM/MFsWm6SA3ClIj
MJPQx+PZFbJmA30Vf28et+MBif6sWLj4XGbhbzCCfd/qqE6C0L1UasP8Pve8JTQP
EcN+BiDC6d1KTmGOuTpvJ2JlUq9L0J/x0hh1qVNRAUPbVo8rH4ZgPcW2N6vqpMdJ
gMH2idtuTPwJOGr9tnF0gCL1WFgwR3tpvMcO+fYz1i4HHfGCqrs4V9KQou/BDrEW
9anKWgH5AgMBAAECggEAAL0/v7uiOSFtGp0zExFq4T4ThQObU71URyuMX+kSg2te
QJpx/KLYhFbZTfhi8LUkEA1hSQ/V93vsFb0MNRWWDuOL0V1LWUvyd3IMECGXBLNM
OMXzDY4bAUTICJsXgj42/jCdDCp5NbGkEEs6l0OWdsF7f6ewL6qFpTwk04WKoyai
KGGQTxAeNPprGp1fJYlsUZkQ1BX/v7ZzI03qIkcajAJlNl/Ypys8ATCSmixYSnpM
sqIvLHVLDlar9tsNpi9MV25y9A5jxwahteEAH0RLsegw0Jnm1dU6ab9FmGmV4/kn
F3clrDtWbyv1rx9Zq7E+CdZ9VgY2gYDFdmpSZWTbAQKBgQDVgKt2tnHFWvlLD/WB
C7FiR8vHuOr+m3kICJQbIHCpZAlfxsCUgAuAGVhM5REcQqnBngWk16jtAWgdAyiL
MCT2xvPLWr5TB3UpS5LVHGmzox5NDVaMr5hHvd4hTdga5t8SeaeF3vkuyuFqCDkD
5fN2AlKHo130VXoCT7jeW73qwQKBgQDUOuZ8VnGa+GDPHvFgSDDLABpnamgHHUPt
SBDCHO7X2xyopaLEQxsyvgR78POrhK05oRFE7ddJga5hHcmt0XYKu9RY+BFuAnI3
AASunZEY5lwYf6eUC3KSy/iCSYvoElfg2gl8leJU77th33qokj/p2ELbW9fx3aFk
kA0eABD9OQKBgAa3q61qhB3fhOR1thW/Vm9vLtwz10D3h1FXY8GOvby2pwzaZgjG
FpaLNZoFwwoOluS+ohLTrj72wl3XUZk/hIo3LEiDrGVUYL1R4WbPJAxA350xBD4c
8D+hm7GUj24ZQX+FUF4H6/Mq8vixFYon3Ackf5BA9Z3QaqxT8c8dN9aBAoGAZnAb
qi5LXYK/r5l+5ntR2dot5HbOyYhNri1XsWonutbPCXQRkWvWp/Jh1bUi2EoNFsDw
xfWLMba/ha7MFvMAaAPrZhoux4u0t2lx2RrC22LtVwHe0C2KWuLLC5AWUKjx890q
MRFjkp24M3CcEtusr+Gru5ekLuFMMm75dd6QVLkCgYEAjgxA1Em3fxTI5IBos7KI
LXK9lrLNlKqUN3ZmApQEWhmf4eclEFP0CouTgqk7I+5wYFu996M+cVloCOdgdXAg
E39cgZfugnFVFB9gmLf5QG4j5V2Koq8Gu9aVQ1kZ8yY83YdwT+XK4kalm20/xYCh
m4S4ReDHenIMShhDLnkPt04=
-----END PRIVATE KEY-----"""

def load_private_key():
    # 1. Check environment variable
    env_pem = os.getenv("PRIVATE_KEY_PEM")
    if env_pem:
        return serialization.load_pem_private_key(
            env_pem.encode("utf-8"),
            password=None,
            backend=default_backend()
        )
    
    # 2. Check local file on disk
    key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "keys", "private_key.pem")
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
            
    # 3. Fallback to default in-code PEM
    return serialization.load_pem_private_key(
        DEFAULT_PRIVATE_KEY_PEM.encode("utf-8"),
        password=None,
        backend=default_backend()
    )

PRIVATE_KEY = load_private_key()
KEY_ID = "gateway-permanent-key-1"
ISSUER = "https://coruscating-croissant-490115.netlify.app"

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
        "iss": ISSUER,
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
