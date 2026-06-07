"""Bastion FastAPI app — health report collector and status endpoint."""

from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth import verify_token, create_token
from models import HealthReport, HostStatus, status_from_age

app = FastAPI(title="Bastion Health API")

# CORS — allow the static GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

security = HTTPBearer()

# In-memory store: hostname -> latest HealthReport + received_at
reports: Dict[str, dict] = {}


# --- Auth dependency ---
def require_host(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate JWT and return the hostname (subject)."""
    try:
        payload = verify_token(credentials.credentials)
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --- Public endpoints ---
@app.get("/health")
def get_health() -> list[HostStatus]:
    """Return status of all known hosts."""
    now = datetime.now(timezone.utc)
    results = []
    for hostname, data in reports.items():
        age = (now - data["received_at"]).total_seconds()
        report = data["report"]
        results.append(
            HostStatus(
                hostname=hostname,
                status=status_from_age(age),
                cpu_percent=report.cpu_percent,
                memory_percent=report.memory_percent,
                disk_percent=report.disk_percent,
                uptime_seconds=report.uptime_seconds,
                last_seen=data["received_at"],
            )
        )
    return sorted(results, key=lambda h: h.hostname)


# --- Secure endpoint for hosts ---
@app.post("/report")
def post_report(report: HealthReport, hostname: str = Depends(require_host)):
    """Submit a health report (JWT required)."""
    now = datetime.now(timezone.utc)
    reports[hostname] = {
        "report": report,
        "received_at": now,
    }
    return {"status": "ok", "hostname": hostname}


# --- Token generation (admin convenience) ---
@app.post("/token")
def generate_token(hostname: str) -> dict:
    """Generate a JWT token for a host. Protect this in production."""
    token = create_token(hostname)
    return {"hostname": hostname, "token": token}


# --- Dev server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
