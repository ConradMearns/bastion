"""Data models for health reports."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class HealthReport(BaseModel):
    """Health data submitted by a host."""

    hostname: str = Field(..., description="Host identifier")
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    disk_percent: float = Field(..., ge=0, le=100)
    uptime_seconds: float = Field(..., ge=0)
    timestamp: Optional[datetime] = None


class HostStatus(BaseModel):
    """Public-facing host status."""

    hostname: str
    status: str  # "healthy", "warning", "down"
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: float
    last_seen: datetime


def status_from_age(age_seconds: float) -> str:
    """Determine status from seconds since last report."""
    if age_seconds < 120:
        return "healthy"
    elif age_seconds < 300:
        return "warning"
    return "down"
