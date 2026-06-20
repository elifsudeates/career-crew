import asyncio
from typing import Dict, TypedDict, Optional
from .models import JobStatus


class ProgressInfo(TypedDict):
    current_agent: str
    current_step: int
    total_steps: int
    started_at: float
    remaining_seconds: Optional[int]


job_store: Dict[str, JobStatus] = {}
log_queues: Dict[str, asyncio.Queue] = {}
progress_store: Dict[str, ProgressInfo] = {}
