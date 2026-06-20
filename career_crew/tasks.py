from crewai import Task


def get_parse_cv_task(agent, cv_content: str):
    return Task(
        description=(
            "Aşağıdaki CV metnindeki TÜM bilgileri çıkar ve yapılandır.\n\n"
            "CV METNİ:\n"
            "```\n"
            f"{cv_content}\n"
            "```\n\n"
            "Çıkar:\n"
            "- NAME: Adayın tam adı (rapor isimlendirmesi için kritik)\n"
            "- HARD SKILLS: Her beceri için tahmini yeterlilik seviyesi ve gerekçesi\n"
            "- SOFT SKILLS: Açıkça belirtilen ve deneyim tanımlarından çıkarılan kişisel beceriler\n"
            "- EXPERIENCE: Her rol için → şirket, unvan, süre, kıdem, 3 maddelik başarı özeti\n"
            "- EDUCATION: Derece, kurum, mezuniyet yılı\n"
            "- CERTIFICATIONS ve önemli ACHIEVEMENTS\n"
            "- RED FLAGS: İstihdam boşlukları, belirsiz unvanlar, ölçülebilir başarı eksikliği, "
            "GitHub/portfolio/LinkedIn yokluğu\n\n"
            "Yapılandırılmış bir JSON objesi döndür."
        ),
        expected_output="Aday adı ve detaylı CV verisi (beceriler, deneyim, eğitim, kırmızı bayraklar) içeren tam yapılandırılmış JSON.",
        agent=agent,
    )


def get_parse_job_task(agent, job_content: str):
    return Task(
        description=(
            "Aşağıdaki iş ilanı metnini analiz et.\n\n"
            "İŞ İLANI METNİ:\n"
            "```\n"
            f"{job_content}\n"
            "```\n\n"
            "KATMAN 1 — AÇIK GEREKSİNİMLER:\n"
            "- Pozisyon başlığı\n"
            "- Tüm gerekli beceriler: ZORUNLU_TEKNİK / TERCİH_TEKNİK / ZORUNLU_KİŞİSEL\n"
            "- Gerekli deneyim yılı\n"
            "- Eğitim ve sertifika gereksinimleri\n"
            "- Lokasyon, uzaktan çalışma politikası, maaş (belirtildiyse)\n\n"
            "KATMAN 2 — GİZLİ SİNYALLER:\n"
            "- Şirket kültürü (startup vs kurumsal, ton analizi)\n"
            "- Yazılı olmayan günlük beklentiler (bu rol GERÇEKTE ne gerektiriyor?)\n"
            "- İlandaki kırmızı bayraklar (yüksek personel devri belirtileri vb.)\n"
            "- ATS anahtar kelimeleri: adayın eleme aşamasını geçmek için MUTLAKA kullanması gereken ifadeler\n\n"
            "ats_keywords dizisi içeren yapılandırılmış bir JSON döndür."
        ),
        expected_output="Açık gereksinimler, gizli sinyaller ve ATS anahtar kelimeleri içeren yapılandırılmış JSON.",
        agent=agent,
    )


def get_gap_task(agent, cv_task, job_task, job_id: str):
    return Task(
        description=(
            "Önceki ajanlardan gelen CV ve iş ilanı verilerini kullanarak kapsamlı bir uyum analizi raporu üret.\n\n"
            "TÜM ANALİZİ TÜRKÇE OLARAK YAZ.\n\n"
            "ADIM 1 — BECERİ EŞLEŞMESİ:\n"
            "İş ilanındaki her zorunlu beceri için aşağıdaki etiketlerden birini kullan:\n"
            "🟢 GÜÇLÜ EŞLEŞME — aday bu beceriye gerekli seviyede açıkça sahip\n"
            "🟡 KISMİ EŞLEŞME — ilgili beceri var ama tam uyum değil\n"
            "🔴 KRİTİK EKSİKLİK — beceri eksik veya yetersiz gelişmiş\n\n"
            "ADIM 2 — UYUMLULUK PUANI (0-100):\n"
            "Şu ağırlıkları kullanarak hesapla:\n"
            "- Zorunlu teknik beceriler: %60\n"
            "- Kişisel beceriler + kültür uyumu: %25\n"
            "- Eğitim + sertifikalar: %15\n"
            "Her alt puanı ve hesaplamayı açıkça göster.\n\n"
            "ADIM 3 — GİZLİ BEKLENTİ UYUMU:\n"
            "Aday, rolün yazılı olmayan kültürel ve günlük beklentileriyle ne kadar uyumlu?\n\n"
            "ADIM 4 — STRATEJİK DEĞERLENDİRME:\n"
            "- Başvuruda vurgulanması gereken en güçlü 3 yön\n"
            "- Başvurmadan önce kapatılması gereken en kritik 3 açık\n"
            "- Karar: Hemen Başvur / Önce Hazırlan / Başvurma\n\n"
            "Raporunu YALNIZCA aşağıdaki Markdown yapısıyla yaz:\n\n"
            "# Uyum Analizi: [Pozisyon Adı]\n\n"
            "## Uyumluluk Puanı: X/100\n\n"
            "### Puan Dökümü\n"
            "| Kategori | Ağırlık | Alt Puan |\n"
            "| --- | --- | --- |\n"
            "| Zorunlu Teknik Beceriler | %60 | X/60 |\n"
            "| Kişisel Beceriler + Kültür Uyumu | %25 | X/25 |\n"
            "| Eğitim + Sertifikalar | %15 | X/15 |\n\n"
            "## Beceri Eşleşme Tablosu\n"
            "| Beceri | Tür | Durum | Notlar |\n"
            "| --- | --- | --- | --- |\n\n"
            "## Güçlü Yanlar 🟢\n\n"
            "## Kısmi Eşleşmeler 🟡\n\n"
            "## Kritik Eksiklikler 🔴\n\n"
            "## Gizli Beklenti Uyumu\n\n"
            "## Stratejik Öneri\n\n"
            "**Vurgulanması Gereken 3 Güçlü Yön:**\n\n"
            "**Başvurmadan Önce Kapatılması Gereken 3 Eksik:**\n\n"
            "**Karar:** Hemen Başvur / Önce Hazırlan / Başvurma"
        ),
        expected_output="Beceri eşleşme tablosu, puan dökümü ve stratejik öneri içeren tam Türkçe Markdown uyum analizi raporu.",
        context=[cv_task, job_task],
        agent=agent,
    )


def get_interview_task(agent, gap_task):
    return Task(
        description=(
            "Önceki ajandan gelen uyum analizini kullanarak bu aday ve rol için ayrıntılı bir mülakat hazırlık rehberi oluştur.\n\n"
            "TÜM İÇERİĞİ TÜRKÇE OLARAK YAZ.\n\n"
            "Tam olarak aşağıdaki yapıyı kullan:\n\n"
            "## 🎯 Mülakat Hazırlık Rehberi\n\n"
            "### 1. Beklenen Zor Sorular\n"
            "Tespit edilen eksikliklere dayanarak mülakatçının MUTLAKA soracağı 5 zor soruyu listele.\n"
            "Her soru için şunları ver:\n"
            "- **Soru** (tam ifadesiyle)\n"
            "- **Neden soruyorlar** — mülakatçının gerçek amacı\n"
            "- **Kazanan cevap stratejisi** — STAR yöntemiyle, role özgü somut bir örnek kullanarak\n\n"
            "### 2. Güçlü Yanlarını Nasıl Vurgularsın\n"
            "Güçlü eşleşmelere dayanarak, adayın proaktif olarak ortaya koyması gereken "
            "3 spesifik konuşma noktasını ver (tam formülasyonlarla).\n\n"
            "### 3. Zayıf Noktalara Hazırlık\n"
            "Her kritik eksiklik için: açığı dürüstçe kabul ederken büyüme zihniyeti ve "
            "proaktif inisiyatif gösteren bir yeniden çerçeveleme stratejisi ver.\n\n"
            "### 4. 30-60-90 Günlük Plan\n"
            "Adayın ilk 30, 60 ve 90 günde yapacaklarını gösteren role özgü, somut bir eylem planı. "
            "'Kendinizi nerede görüyorsunuz?' sorusunu önceden yanıtlar ve ciddiyeti gösterir.\n\n"
            "### 5. Mülakatçıya Sorulacak Sorular\n"
            "Stratejik düşünceyi gösteren, adayın mülakatçıya sorabileceği 3 akıllı soru "
            "(her sorunun neden etkileyici olduğunu da açıkla).\n\n"
            "Genel mülakat tavsiyeleri değil, gerçek uyum analizine dayalı, son derece spesifik içerik üret."
        ),
        expected_output="Hedeflenmiş sorular, stratejiler, 30-60-90 günlük plan ve mülakatçıya sorulacak sorular içeren ayrıntılı Türkçe mülakat hazırlık rehberi.",
        context=[gap_task],
        agent=agent,
    )


def get_translate_task(agent, gap_task, interview_task, job_id: str):
    return Task(
        description=(
            "Önceki iki ajandan gelen iki ayrı bölümü okudun:\n"
            "1. Uyum Analizi (Uyum Analisti'nden)\n"
            "2. Mülakat Hazırlık Rehberi (Mülakat Koçu'ndan)\n\n"
            "Görevin: Bu iki bölümü BİR TEK, tutarlı ve eksiksiz Türkçe raporda birleştir ve cilala.\n\n"
            "Kurallar:\n"
            "- İki bölümü de EKSIKSIZ ve SIRASINDA dahil et — hiçbir şeyi kısaltma veya atlama\n"
            "- Tüm Markdown biçimini koru: başlıklar, tablolar, kalın metin, listeler\n"
            "- Tüm emojileri olduğu gibi bırak: 🟢 🟡 🔴 🎯 📋\n"
            "- Kalan İngilizce ifadeleri Türkçeye çevir\n"
            "- Başlık tutarlılığını kontrol et ve gerekirse düzelt\n"
            "- Sıra: önce Uyum Analizi, ardından --- ile ayrılmış Mülakat Hazırlık Rehberi\n"
            "- YALNIZCA birleştirilmiş Markdown çıktısını ver. Giriş açıklaması veya meta yorum ekleme."
        ),
        expected_output="Uyum analizi ve mülakat hazırlık rehberini birleştiren eksiksiz, tek parça Türkçe Markdown raporu.",
        context=[gap_task, interview_task],
        agent=agent,
    )
