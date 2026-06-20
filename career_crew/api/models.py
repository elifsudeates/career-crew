from pydantic import BaseModel
from typing import Optional, List

class Phase1Request(BaseModel):
    cv_text: str
    job_text: str
    llm_provider: str = "ollama"   # "ollama" | "gemini" | "openai" | "anthropic"
    model_name: Optional[str] = None
    api_key: Optional[str] = None

class ConnectionTestRequest(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None

class LLMModel(BaseModel):
    name: str
    details: Optional[str] = None

class LLMModelsResponse(BaseModel):
    provider: str
    models: List[LLMModel]

class JobStatus(BaseModel):
    job_id: str
    status: str           # "pending" | "running" | "completed" | "failed"
    phase: int
    created_at: str
    completed_at: Optional[str] = None
    report_files: List[str] = []
    error: Optional[str] = None

class ReportResponse(BaseModel):
    filename: str
    content: str
    created_at: str
