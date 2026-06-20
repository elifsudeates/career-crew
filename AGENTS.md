# CareerCrew — Ajan ve Görev Dokümantasyonu

Sistem 5 ajandan oluşur. Her ajan sırayla çalışır; bir öncekinin çıktısı sonrakine bağlam olarak geçer.

---

## Akış Diyagramı

```
CV Dosyası ──┐
              ├──► [1] CV Analisti ──► JSON (Python içinde okunur, göreve gömülür)
İş İlanı ────┘

İş İlanı ──────► [2] İş İlanı Analisti ──► JSON

CV JSON + İş JSON ──► [3] Uyum Analisti ──► Markdown Gap Analizi (TÜRKÇE)

Gap Analizi ──────► [4] Mülakat Koçu ──► Markdown Mülakat Rehberi (TÜRKÇE)

Gap + Mülakat ────► [5] Rapor Derleyici ──► Birleşik Türkçe Rapor

────────────────────────────────────────────────────────────────────
Post-Processing (crew bitince):
  - translate_task (Rapor Derleyici) çıktısı > 500 karakter ise kullanılır
  - Değilse: gap_task + interview_task doğrudan birleştirilir
  - Her ikisi de yetersizse: LLM'e doğrudan Türkçe çağrı yapılır (fallback)
  - YALNIZCA Türkçe rapor dosyaya kaydedilir
```

---

## [1] CV Analisti — `CV Analizi` adımı

| Özellik | Değer |
| --- | --- |
| **Sınıf adı** | `get_cv_parser(llm)` — `agents.py` |
| **Agent name** | `CV Analisti` |
| **Rol** | Senior Technical Recruiter with 15 years of experience |
| **Araç** | Yok (içerik Python tarafından okunur, görev açıklamasına gömülür) |
| **Girdi** | CV metni — `crew_runner.py` tarafından dosyadan okunur, göreve gömülür |
| **Çıktı formatı** | Yapılandırılmış JSON |

**Görev (`get_parse_cv_task`):**
- CV dosyasını verilen path'ten okur
- Şu alanları çıkarır: `NAME`, `HARD_SKILLS`, `SOFT_SKILLS`, `EXPERIENCE`, `EDUCATION`, `CERTIFICATIONS`, `RED_FLAGS`
- Her deneyim için: şirket, unvan, süre, kıdem seviyesi, 3 maddelik özet
- Kırmızı bayraklar: istihdam boşlukları, ölçülebilir başarı yokluğu, portfolio/GitHub yokluğu

---

## [2] İş İlanı Analisti — `İş İlanı Analizi` adımı

| Özellik | Değer |
| --- | --- |
| **Sınıf adı** | `get_job_analyst(llm)` — `agents.py` |
| **Agent name** | `İş İlanı Analisti` |
| **Rol** | Hiring Manager Psychologist and Job Market Intelligence Specialist |
| **Araç** | Yok (içerik Python tarafından okunur, görev açıklamasına gömülür) |
| **Girdi** | İş ilanı metni — URL'den Jina.ai ile veya doğrudan girdi olarak alınır |
| **Çıktı formatı** | Yapılandırılmış JSON + `ats_keywords` dizisi |

**Görev (`get_parse_job_task`):**
- **Katman 1 (Açık):** Pozisyon başlığı, beceriler (`HARD_REQUIRED / HARD_PREFERRED / SOFT_REQUIRED`), deneyim yılı, eğitim, lokasyon, maaş
- **Katman 2 (Gizli):** Şirket kültürü analizi, gerçek günlük beklentiler, ATS anahtar kelimeleri, ilandaki kırmızı bayraklar

---

## [3] Uyum Analisti — `Uyum Analizi` adımı

| Özellik | Değer |
| --- | --- |
| **Sınıf adı** | `get_gap_detector(llm)` — `agents.py` |
| **Agent name** | `Uyum Analisti` |
| **Rol** | Career Intelligence Analyst and Match Scoring Expert |
| **Araç** | Yok (araç kullanmaz) |
| **Bağlam** | `cv_task` + `job_task` çıktıları |
| **Çıktı formatı** | Markdown raporu |

**Görev (`get_gap_task`):**

4 adımda çalışır:

1. **Beceri Eşleşmesi:** Her gerekli beceri için etiket atar:
   - 🟢 `STRONG MATCH` — aday açıkça bu seviyede
   - 🟡 `PARTIAL MATCH` — ilişkili ama tam değil
   - 🔴 `CRITICAL GAP` — eksik veya yetersiz
2. **Uyumluluk Puanı (0-100):**
   - Zorunlu teknik beceriler: %60
   - Yumuşak beceriler + kültür uyumu: %25
   - Eğitim + sertifika: %15
3. **Gizli Beklenti Uyumu:** Yazılı olmayan kültür ve iş beklentileriyle uyum değerlendirmesi
4. **Stratejik Değerlendirme:** Vurgulama önerileri, kapatılacak açıklar, karar (Hemen Başvur / Önce Hazırlan / Başvurma)

**Çıktı yapısı:**
```markdown
# Gap Analysis: [Pozisyon]
## Compatibility Score: X/100
### Score Breakdown (tablo)
## Skill Match Table (tablo)
## Strong Points 🟢
## Partial Matches 🟡
## Critical Gaps 🔴
## Hidden Expectation Alignment
## Strategic Recommendation
```

---

## [4] Mülakat Koçu — `Mülakat Soruları` adımı

| Özellik | Değer |
| --- | --- |
| **Sınıf adı** | `get_interview_coach(llm)` — `agents.py` |
| **Agent name** | `Mülakat Koçu` |
| **Rol** | Senior Interview Coach and Career Strategist |
| **Araç** | Yok |
| **Bağlam** | `gap_task` çıktısı |
| **Çıktı formatı** | Markdown — TÜRKÇE (başından itibaren Türkçe yazar) |

**Görev (`get_interview_task`):**

5 bölümlü Türkçe mülakat hazırlık rehberi üretir:

1. **Beklenen Zor Sorular** — 5 zor soru, her biri için: soru metni, neden sorulduğu, STAR formatıyla kazanan cevap stratejisi
2. **Güçlü Yanlarını Nasıl Vurgularsın** — 3 proaktif konuşma noktası (tam formülasyonla)
3. **Zayıf Noktalara Hazırlık** — Her kritik açık için "büyüme zihniyeti" yeniden çerçeveleme stratejisi
4. **30-60-90 Günlük Plan** — Role özgü ilk 90 günlük eylem planı
5. **Mülakatçıya Sorulacak Sorular** — Stratejik düşünmeyi gösteren 3 akıllı soru

---

## [5] Rapor Derleyici — `Rapor Derleme` adımı

| Özellik | Değer |
| --- | --- |
| **Sınıf adı** | `get_translator(llm)` — `agents.py` |
| **Agent name** | `Rapor Derleyici` |
| **Rol** | Senior Career Report Editor and Compiler |
| **Araç** | Yok |
| **Bağlam** | `gap_task` + `interview_task` çıktıları |
| **Çıktı formatı** | Birleşik Türkçe Markdown raporu |

**Görev (`get_translate_task`):**

- Uyum analizini ve mülakat rehberini tek, tutarlı bir Türkçe belgede birleştirir
- Tüm Markdown formatı (tablolar, başlıklar, kalın) korunur
- Emojiler olduğu gibi bırakılır: 🟢 🟡 🔴 🎯 📋
- Kalan İngilizce ifadeleri Türkçeye çevirir
- Sıra: Uyum Analizi → `---` → Mülakat Hazırlık Rehberi

---

## Dosya Çıktısı

| Özellik | Detay |
| --- | --- |
| **Kaydedilen dosya** | Yalnızca Türkçe rapor (`reports/` klasörü) |
| **Format** | `YYYY-MM-DD_Aday_Pozisyon_Model.md` |
| **Örnek** | `2026-06-06_Cagatay_Uresin_Senior_Backend_gpt_oss_120b_cloud.md` |
| **İçerik** | Uyum Analizi + Mülakat Rehberi + İş İlanı Özeti |

---

## API Akışı

```
POST /api/phase1          → Analizi başlatır (FormData: cv_file, job_url, llm_provider, model_name, ...)
GET  /api/logs/{job_id}   → SSE stream (agent_start, agent_done, log, done olayları)
GET  /api/status/{job_id} → Mevcut iş durumu + report_files listesi
GET  /api/reports         → Tüm raporların listesi
GET  /api/reports/{name}  → Rapor içeriği (Markdown)
GET  /api/reports/{name}/pdf → PDF olarak indir
```

---

## SSE Olay Formatı

```json
{ "type": "agent_start", "agent": "CV Analizi", "step": 1, "total": 5, "remaining": 185 }
{ "type": "agent_done",  "agent": "CV Analizi", "step": 1, "total": 5, "elapsed": 23 }
{ "type": "log",         "data": "[CV Analisti] ..." }
{ "type": "done" }
```

---

## Fallback Mekanizması

Büyük modeller (gpt-oss:120b-cloud, qwen3.5:397b-cloud) genellikle ajan çıktısını düzgün üretir.
Küçük modeller (llama3.1:8b vb.) bazen boş veya çok kısa çıktı üretir.
Bu durumda `crew_runner.py` iki fallback adım uygular:

1. `gap_task.output.raw < 300 karakter` → `_generate_report_directly()` ile sıfırdan üretilir
2. `translate_task.output.raw < 500 karakter` → `_translate_to_turkish()` ile doğrudan çevrilir
