import asyncio
import os
import time
import json
import re
from datetime import datetime
from crewai import Crew
from config import get_llm, REPORTS_DIR, get_active_model_name
from api.store import job_store, log_queues, progress_store
from agents import get_cv_parser, get_job_analyst, get_gap_detector, get_interview_coach, get_translator
from tasks import get_parse_cv_task, get_parse_job_task, get_gap_task, get_interview_task, get_translate_task


def _generate_report_directly(llm, cv_output: str, job_output: str) -> str:
    """Fallback: generate Turkish gap analysis directly when gap_task output is insufficient."""
    prompt = f"""Sen bir kariyer analistisin. Aşağıdaki CV ve iş ilanı verilerini kullanarak
kapsamlı bir Uyum Analizi raporu yaz. YALNIZCA Markdown raporu çıktıla —
giriş açıklaması, yorum veya kod bloğu ekleme.

=== CV VERİSİ ===
{cv_output}

=== İŞ İLANI VERİSİ ===
{job_output}

Tam olarak şu yapıyı kullan:

# Uyum Analizi: [Pozisyon Adı]

## Uyumluluk Puanı: X/100

### Puan Dökümü
| Kategori | Ağırlık | Alt Puan |
| --- | --- | --- |
| Zorunlu Teknik Beceriler | %60 | X/60 |
| Kişisel Beceriler + Kültür Uyumu | %25 | X/25 |
| Eğitim + Sertifikalar | %15 | X/15 |

## Beceri Eşleşme Tablosu
| Beceri | Tür | Durum | Notlar |
| --- | --- | --- | --- |
| ... | ZORUNLU_TEKNİK | 🟢/🟡/🔴 | ... |

## Güçlü Yanlar 🟢
- ...

## Kısmi Eşleşmeler 🟡
- ...

## Kritik Eksiklikler 🔴
- ...

## Gizli Beklenti Uyumu
...

## Stratejik Öneri

**Vurgulanması Gereken 3 Güçlü Yön:**
1. ...

**Başvurmadan Önce Kapatılması Gereken 3 Eksik:**
1. ...

**Karar:** Hemen Başvur / Önce Hazırlan / Başvurma
"""
    response = llm.call([{"role": "user", "content": prompt}])
    return response if isinstance(response, str) else str(response)


_TR_TO_ASCII = str.maketrans(
    'çğıöşüÇĞİÖŞÜ',
    'cgiosuCGIOSU'
)


def _sanitize_filename(text: str) -> str:
    s = text.translate(_TR_TO_ASCII)
    s = re.sub(r'[\s\-/\\:;*?"<>|]+', '_', s)
    s = re.sub(r'[^\w\._]', '', s)
    return s.strip('_')[:80]


def _extract_from_json(text: str, keys: list) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {k: data.get(k) for k in keys if k in data}
    except Exception:
        pass
    results = {}
    for key in keys:
        pattern = rf'"{key}"\s*:\s*"([^"]+)"'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[key] = match.group(1)
    return results


async def run_phase1(job_id: str, cv_path: str, job_path: str, provider: str = None,
                     model: str = None, api_key: str = None,
                     candidate_name_hint: str = None, job_title_hint: str = None,
                     ollama_base_url: str = None):
    job_store[job_id].status = "running"

    llm = get_llm(provider=provider, model=model, api_key=api_key, base_url=ollama_base_url)
    model_name_for_file = get_active_model_name(provider=provider, model=model)

    cv_parser = get_cv_parser(llm)
    job_analyst = get_job_analyst(llm)
    gap_detector = get_gap_detector(llm)
    coach = get_interview_coach(llm)
    translator = get_translator(llm)

    # Read file contents here — agents no longer need FileReaderTool for input files
    cv_content_text = open(cv_path, encoding="utf-8").read()
    job_content_text = open(job_path, encoding="utf-8").read()

    cv_task = get_parse_cv_task(cv_parser, cv_content_text)
    job_task = get_parse_job_task(job_analyst, job_content_text)
    gap_task = get_gap_task(gap_detector, cv_task, job_task, job_id)
    interview_task = get_interview_task(coach, gap_task)
    translate_task = get_translate_task(translator, gap_task, interview_task, job_id)

    TASK_SEQUENCE = [
        ("CV Analizi",       25),
        ("İş İlanı Analizi", 25),
        ("Uyum Analizi",     60),
        ("Mülakat Soruları", 45),
        ("Rapor Derleme",    30),
    ]
    TOTAL_STEPS = len(TASK_SEQUENCE)

    def _emit(payload: dict):
        log_queues[job_id].put_nowait(payload)

    def step_callback(agent_output):
        try:
            # Extract agent name: try multiple attribute paths
            agent_name = getattr(agent_output, 'agent', None)
            if agent_name is None:
                agent_name = getattr(agent_output, 'name', 'Ajan')
            if hasattr(agent_name, 'name'):
                agent_name = agent_name.name
            elif hasattr(agent_name, 'role'):
                agent_name = agent_name.role

            output_text = (
                getattr(agent_output, 'output', None)
                or getattr(agent_output, 'result', None)
                or getattr(agent_output, 'text', None)
                or str(agent_output)
            )
            snippet = str(output_text)[:180].replace('\n', ' ')
            if len(str(output_text)) > 180:
                snippet += "..."
            _emit({"type": "log", "data": f"[{agent_name}] {snippet}"})
        except Exception:
            _emit({"type": "log", "data": f"[Ajan] Adım tamamlandı"})

    task_index       = [0]
    task_step_starts = {}   # idx -> wall-clock start time
    task_step_starts[0] = None  # filled after start_time is set

    def _scaled_remaining(from_idx: int) -> int:
        """Estimate remaining seconds scaled by actual vs. expected elapsed time."""
        completed = task_index[0]  # number of tasks done so far
        if completed == 0:
            return sum(t[1] for t in TASK_SEQUENCE[from_idx:])

        total_expected_done = sum(TASK_SEQUENCE[i][1] for i in range(completed))
        total_actual_done   = round(time.time() - start_time)
        scale = total_actual_done / total_expected_done if total_expected_done > 0 else 1.0
        # Cap scale: never go below 0.5x or above 5x to avoid wild swings
        scale = max(0.5, min(scale, 5.0))
        return round(sum(t[1] * scale for t in TASK_SEQUENCE[from_idx:]))

    def task_callback(task_output):
        idx = task_index[0]
        elapsed = round(time.time() - start_time)
        if idx < TOTAL_STEPS:
            agent_label, _ = TASK_SEQUENCE[idx]
            task_elapsed = round(time.time() - (task_step_starts.get(idx) or start_time))
            remaining = _scaled_remaining(idx + 1)
            _emit({
                "type": "agent_done",
                "agent": agent_label,
                "step": idx + 1,
                "total": TOTAL_STEPS,
                "elapsed": elapsed,
                "task_elapsed": task_elapsed,
                "remaining": remaining,
                "data": f"[{agent_label}] tamamlandı ({task_elapsed}s)",
            })
            progress_store[job_id] = {
                "current_agent": agent_label,
                "current_step": idx + 1,
                "total_steps": TOTAL_STEPS,
                "started_at": start_time,
                "remaining_seconds": remaining,
            }
        task_index[0] += 1
        next_idx = task_index[0]
        task_step_starts[next_idx] = time.time()
        if next_idx < TOTAL_STEPS:
            next_label, _ = TASK_SEQUENCE[next_idx]
            next_remaining = _scaled_remaining(next_idx)
            _emit({
                "type": "agent_start",
                "agent": next_label,
                "step": next_idx + 1,
                "total": TOTAL_STEPS,
                "elapsed": elapsed,
                "remaining": next_remaining,
                "data": f"[{next_label}] başlıyor...",
            })

    start_time = time.time()
    task_step_starts[0] = start_time   # record first task start

    first_label = TASK_SEQUENCE[0][0]
    first_remaining = sum(t[1] for t in TASK_SEQUENCE)
    _emit({
        "type": "agent_start",
        "agent": first_label,
        "step": 1,
        "total": TOTAL_STEPS,
        "elapsed": 0,
        "remaining": first_remaining,
        "data": f"[{first_label}] başlıyor...",
    })
    progress_store[job_id] = {
        "current_agent": first_label,
        "current_step": 1,
        "total_steps": TOTAL_STEPS,
        "started_at": start_time,
        "remaining_seconds": first_remaining,
    }

    try:
        crew = Crew(
            agents=[cv_parser, job_analyst, gap_detector, coach, translator],
            tasks=[cv_task, job_task, gap_task, interview_task, translate_task],
            verbose=True,
            step_callback=step_callback,
            task_callback=task_callback,
        )

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, crew.kickoff)

        duration_mins = round((time.time() - start_time) / 60, 1)
        tr_duration_text = f"**Analiz Süresi:** {duration_mins} dakika"

        # ── Collect task outputs (all in Turkish now) ─────────────────
        gap_raw       = (getattr(gap_task.output,       "raw", "") or "").strip()
        interview_raw = (getattr(interview_task.output, "raw", "") or "").strip()
        compile_raw   = (getattr(translate_task.output, "raw", "") or "").strip()

        _emit({"type": "log", "data": f"[System] gap={len(gap_raw)}c mulakat={len(interview_raw)}c derle={len(compile_raw)}c"})

        # ── Best case: use compiled (combined) output from 5th agent ──
        if len(compile_raw) > 500:
            tr_content = compile_raw
            _emit({"type": "log", "data": "[System] Derleyici ajan çıktısı kullanıldı."})

        # ── Fallback 1: combine gap + interview directly ───────────────
        elif len(gap_raw) > 300:
            tr_content = gap_raw
            if interview_raw and len(interview_raw) > 100:
                tr_content += "\n\n---\n\n" + interview_raw
            _emit({"type": "log", "data": "[System] Gap + mülakat doğrudan birleştirildi."})

        # ── Fallback 2: generate from scratch (Turkish prompt) ────────
        else:
            _emit({"type": "log", "data": "[System] Ajan çıktıları yetersiz, doğrudan üretiliyor..."})
            cv_raw  = (getattr(cv_task.output,  "raw", "") or "")
            job_raw = (getattr(job_task.output, "raw", "") or "")
            tr_content = await loop.run_in_executor(None, _generate_report_directly, llm, cv_raw, job_raw)
            if interview_raw and len(interview_raw) > 100:
                tr_content += "\n\n---\n\n" + interview_raw

        # ── Build filename ────────────────────────────────────────────
        cv_raw_text = (getattr(cv_task.output, "raw", "") or "")
        job_raw_text = (getattr(job_task.output, "raw", "") or "")

        cv_info = _extract_from_json(cv_raw_text, ["NAME", "name"])
        job_info = _extract_from_json(job_raw_text, ["Position title", "position_title", "title"])

        candidate_name = (
            candidate_name_hint
            or cv_info.get("NAME") or cv_info.get("name")
            or "Aday"
        )
        job_title = (
            job_title_hint
            or job_info.get("Position title") or job_info.get("position_title") or job_info.get("title")
            or "Pozisyon"
        )

        date_str = datetime.now().strftime("%Y-%m-%d")
        base_name = _sanitize_filename(
            f"{date_str}_{candidate_name}_{job_title}_{model_name_for_file}"
        )
        report_filename = f"{base_name}.md"
        report_path = os.path.join(REPORTS_DIR, report_filename)

        # ── Job posting summary block ─────────────────────────────────
        job_source_text = open(job_path, encoding="utf-8").read()
        job_preview = job_source_text[:600].strip()
        if len(job_source_text) > 600:
            job_preview += "..."
        job_summary_block = (
            f"\n\n---\n\n"
            f"## 📋 Analiz Edilen İş İlanı\n\n"
            f"> *Aşağıdaki metin Jina.ai veya doğrudan girdi üzerinden alınmıştır.*\n\n"
            f"```\n{job_preview}\n```\n\n---\n\n"
        )

        # ── Save ONLY Turkish report ──────────────────────────────────
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(
                f"<!-- Oluşturulma Tarihi: {timestamp} -->\n"
                f"{tr_duration_text}\n\n"
                f"{tr_content}"
                f"{job_summary_block}"
            )

        _emit({"type": "log", "data": f"[System] Türkçe rapor kaydedildi: {report_filename}"})

        job_store[job_id].status = "completed"
        job_store[job_id].report_files = [report_filename]
        job_store[job_id].completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")

    except Exception as e:
        job_store[job_id].status = "failed"
        job_store[job_id].error = str(e)
        if job_id in log_queues:
            log_queues[job_id].put_nowait({
                "type": "log",
                "data": f"[System] İş başarısız: {str(e)}"
            })
    finally:
        if job_id in log_queues:
            log_queues[job_id].put_nowait({"type": "done"})
