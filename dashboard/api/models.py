from pydantic import BaseModel
from typing import List, Optional, Dict

class HealthCheckSummary(BaseModel):
    total: int
    ok: int
    warnings: int
    critical: int
    errors: int
    status: str  # OK, WARNING, CRITICAL

class BackupJob(BaseModel):
    session_key: int
    start_time: str
    end_time: str
    status: str
    input_type: str
    output_gb: float
    elapsed_minutes: float

class DiskGroup(BaseModel):
    name: str
    state: str
    total_gb: float
    used_gb: float
    free_gb: float
    used_pct: float

class ASMCapacityStats(BaseModel):
    diskgroups: List[DiskGroup]
    alerts: List[Dict]

class SystemStatus(BaseModel):
    hostname: str
    platform: str
    version: str = "1.0.0"
