from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from app.routers import s3, redshift, postgres, auth
except ModuleNotFoundError:
    from api.app.routers import s3, redshift, postgres, auth

app = FastAPI(
    title="Secure Data Service API",
    description="Enterprise Data Service exposing S3, Redshift, and PostgreSQL tools for AgentCore Gateway.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(s3.router)
app.include_router(redshift.router)
app.include_router(postgres.router)
app.include_router(auth.router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "SecureDataService"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
