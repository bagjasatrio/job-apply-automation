from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    APPLIED = "Applied"
    ON_PROGRESS = "On Progress"
    REJECTED = "Rejected"
    OFFERING = "Offering"

class ApplicationRecord(BaseModel):
    company: str
    position: str
    channel: str  # Email, LinkedIn, Glints, Jobstreet
    status: JobStatus = JobStatus.APPLIED
    contact: Optional[str] = None
    date_applied: datetime = Field(default_factory=datetime.now)
    notes: str = ""
