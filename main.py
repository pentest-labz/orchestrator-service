from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
import httpx
from jose import JWTError, jwt
import os

# load your JWT secret (in real deploy, use env var or mounted secret)
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(
    title="Orchestrator Service",
    version="2.0.0",
    description="Backend orchestrator with JWT auth"
)

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload  # you can attach user info here
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.get("/scan")
async def trigger_scan(target: str, scan_type: str, version: bool = False, ports: str | None = None, user=Depends(verify_token)):
    scanner_url = "http://scanner:8001/scan"
    params = {"target": target, "scan_type": scan_type, "version": str(version).lower()}
    if scan_type == "custom":
        if not ports:
            raise HTTPException(status_code=400, detail="`ports` is required for custom scans")
        params["ports"] = ports

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(scanner_url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return JSONResponse(status_code=exc.response.status_code, content={"scanner_error": exc.response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call scanner service: {e}")

@app.get("/health")
async def health(user=Depends(verify_token)):
    return {"status": "ok"}
