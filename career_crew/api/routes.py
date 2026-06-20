import os
import io
import json
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form, Request
from sse_starlette.sse import EventSourceResponse

import tempfile
import httpx
import pdfplumber
try:
    import docx as python_docx
except ImportError:
    python_docx = None

from config import (
    INPUTS_DIR, REPORTS_DIR, LLM_PROVIDER,
    GEMINI_MODELS, OLLAMA_BASE_URL,
    OPENAI_API_KEY, OPENAI_MODELS,
    ANTHROPIC_MODELS, JINA_API_KEY,
    get_llm,
)
from url_extractor import extract_job_from_url
from pdf_exporter import markdown_to_pdf
from .models import JobStatus, ReportResponse, ConnectionTestRequest, LLMModelsResponse, LLMModel
from .store import job_store, log_queues, progress_store
from crew_runner import run_phase1
from settings_db import get_all as db_get_settings, upsert as db_upsert_settings

router = APIRouter()


@router.get("/settings")
async def get_settings():
    return db_get_settings()


@router.post("/settings")
async def save_settings(request: Request):
    data = await request.json()
    db_upsert_settings(data)
    return {"status": "ok"}


@router.post("/phase1", response_model=JobStatus)
async def start_phase1(
    background_tasks: BackgroundTasks,
    cv_file: UploadFile = File(None),
    cv_text: str = Form(None),
    job_file: UploadFile = File(None),
    job_url: str = Form(None),
    job_text: str = Form(None),
    llm_provider: str = Form("ollama"),
    model_name: str = Form(None),
    api_key: str = Form(None),
    candidate_name: str = Form(None),
    job_title_hint: str = Form(None),
    jina_api_key: str = Form(None),
    ollama_base_url: str = Form(None),
):
    job_id = str(uuid.uuid4())

    def _extract_file(raw: bytes, filename: str, label: str) -> str:
        fname = filename.lower()
        try:
            if fname.endswith(".pdf"):
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages).strip()
                if not text:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"{label} PDF'inden metin okunamadı. "
                            "Bu PDF taranmış görsel (OCR) olabilir. "
                            "Lütfen metni kopyalayıp 'Metin' sekmesine yapıştırın."
                        ),
                    )
                return text
            elif fname.endswith(".docx") and python_docx:
                doc = python_docx.Document(io.BytesIO(raw))
                return "\n".join(p.text for p in doc.paragraphs).strip()
            else:
                return raw.decode("utf-8", errors="replace").strip()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"{label} dosyası okunamadı: {str(e)}")

    # --- Extract CV text (file > text) ---
    cv_content = None
    if cv_file and cv_file.filename:
        cv_content = _extract_file(await cv_file.read(), cv_file.filename, "CV")

    if not cv_content:
        cv_content = (cv_text or "").strip()

    if not cv_content:
        raise HTTPException(status_code=400, detail="CV içeriği gerekli — dosya yükleyin veya metin yapıştırın.")

    # --- Extract Job Posting text (file > URL > text) ---
    job_content = None
    if job_file and job_file.filename:
        job_content = _extract_file(await job_file.read(), job_file.filename, "İş ilanı")

    if not job_content and job_url:
        try:
            job_content = await extract_job_from_url(
                job_url, api_key=jina_api_key or JINA_API_KEY
            )
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"URL çekme başarısız: {str(e)}")

    if not job_content:
        job_content = (job_text or "").strip()

    if not job_content:
        raise HTTPException(status_code=400, detail="İş ilanı gerekli — dosya yükleyin, URL girin veya metin yapıştırın.")

    # Save inputs to disk
    cv_path = os.path.join(INPUTS_DIR, f"cv_{job_id}.txt")
    job_path = os.path.join(INPUTS_DIR, f"job_{job_id}.txt")
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(cv_content)
    with open(job_path, "w", encoding="utf-8") as f:
        f.write(job_content)

    # Initialize job store
    job_store[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        phase=1,
        created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        report_files=[]
    )
    log_queues[job_id] = asyncio.Queue()

    background_tasks.add_task(
        run_phase1,
        job_id,
        cv_path,
        job_path,
        llm_provider,
        model_name,
        api_key,
        candidate_name,
        job_title_hint,
        ollama_base_url or None,
    )

    return job_store[job_id]


@router.get("/llm/models", response_model=LLMModelsResponse)
async def list_llm_models(provider: str, api_key: str = None, ollama_base_url: str = None):
    p = provider.lower()
    models = []
    _ollama_url = ollama_base_url or OLLAMA_BASE_URL

    if p == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{_ollama_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    for m in data.get("models", []):
                        models.append(LLMModel(
                            name=m["name"],
                            details=m.get("details", {}).get("parameter_size")
                        ))
        except Exception:
            pass
    elif p == "gemini":
        for m in GEMINI_MODELS:
            models.append(LLMModel(name=m))
    elif p == "openai":
        key = api_key or OPENAI_API_KEY
        if key:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {key}"},
                        timeout=5.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        chat_models = sorted(
                            m["id"] for m in data.get("data", [])
                            if m["id"].startswith(("gpt-4", "gpt-3", "o1", "o3"))
                            and "instruct" not in m["id"]
                        )
                        for m in chat_models:
                            models.append(LLMModel(name=m))
            except Exception:
                pass
        if not models:
            for m in OPENAI_MODELS:
                models.append(LLMModel(name=m))
    elif p == "anthropic":
        for m in ANTHROPIC_MODELS:
            models.append(LLMModel(name=m))

    return LLMModelsResponse(provider=provider, models=models)


@router.post("/llm/test")
async def test_llm_connection(request: ConnectionTestRequest):
    try:
        llm = get_llm(provider=request.provider, model=request.model, api_key=request.api_key)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, llm.call, [{"role": "user", "content": "hi"}])
        if response:
            return {"status": "success", "message": "Connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Unknown error during connection test"}


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_store[job_id]


@router.get("/reports")
async def list_reports():
    reports = []
    if os.path.exists(REPORTS_DIR):
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith(".md"):
                filepath = os.path.join(REPORTS_DIR, filename)
                size_kb = round(os.path.getsize(filepath) / 1024, 2)
                created_at = datetime.fromtimestamp(
                    os.path.getctime(filepath)
                ).strftime("%Y-%m-%dT%H:%M:%S")
                reports.append({
                    "filename": filename,
                    "size_kb": size_kb,
                    "created_at": created_at
                })
    return reports


@router.get("/reports/{filename}/pdf")
async def download_report_pdf(filename: str):
    from fastapi.responses import Response
    from urllib.parse import quote

    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath) or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Report not found")

    with open(filepath, "r", encoding="utf-8") as f:
        md_content = f.read()

    pdf_name = filename.replace(".md", ".pdf")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    try:
        markdown_to_pdf(md_content, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF oluşturma hatası: {str(e)}")

    with open(tmp.name, "rb") as f:
        pdf_bytes = f.read()
    os.unlink(tmp.name)

    # RFC 5987 encoding — handles Turkish and other non-ASCII chars in header
    encoded_name = quote(pdf_name.encode("utf-8"))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.get("/reports/{filename}", response_model=ReportResponse)
async def get_report(filename: str):
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath) or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Report not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    created_at = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y-%m-%dT%H:%M:%S")
    return ReportResponse(filename=filename, content=content, created_at=created_at)


@router.get("/logs/{job_id}")
async def get_logs(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_id not in log_queues:
        raise HTTPException(status_code=404, detail="Logs not found for this job")

    async def event_generator():
        queue = log_queues[job_id]
        try:
            while True:
                log_entry = await queue.get()
                event_type = log_entry.get("type", "log")
                if event_type == "done":
                    yield {"event": "done", "data": "Job completed"}
                    break
                elif event_type in ("agent_start", "agent_done"):
                    yield {"event": event_type, "data": json.dumps(log_entry)}
                else:
                    yield {"event": "log", "data": log_entry.get("data", "")}
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return progress_store.get(job_id, {})


@router.get("/health")
async def get_health():
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "version": "1.0.0"
    }
