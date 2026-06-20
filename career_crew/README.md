# Career Crew: Yapay Zeka Destekli Kariyer Analiz Asistanı

Bu proje, bir CV'yi belirli bir iş ilanıyla karşılaştırmak, eksiklikleri (gap analizi) belirlemek ve adaya stratejik tavsiyeler sunmak için CrewAI çerçevesini kullanan çok ajanlı bir sistemdir. FastAPI tabanlı bir web arayüzü üzerinden çalışır ve sonuçları profesyonel bir Türkçe rapor olarak sunar.

## 🚀 Proje Ne Yapıyor?

Kullanıcı bir CV ve bir iş ilanı metni sağladığında, sistem şunları gerçekleştirir:
1.  **CV Analizi:** CV'deki yetkinlikleri, deneyimleri ve potansiyel riskleri yapılandırılmış bir veri haline getirir.
2.  **İş İlanı Analizi:** İş ilanındaki açık ve gizli gereksinimleri (şirket kültürü, ATS anahtar kelimeleri vb.) deşifre eder.
3.  **Gap (Eksiklik) Analizi:** Adayın profili ile iş ilanı arasındaki uyumu 0-100 arası bir puanla değerlendirir.
4.  **Türkçe Raporlama:** Tüm teknik bulguları ve stratejik önerileri profesyonel bir Türkçe rapora dönüştürür.

## 🛠️ Nasıl Çalışıyor?

Sistem, **CrewAI** kütüphanesi sayesinde birbirleriyle iletişim kuran ve belirli görevleri yerine getiren dört uzman ajan üzerine kuruludur:

1.  **Veri Girişi:** Dosya okuyucu araçlar (`file_reader_tool`) kullanılarak CV ve iş ilanı içeriği sisteme yüklenir.
2.  **Sıralı Görev Dağılımı:** Ajanlar, tanımlanmış görevleri (`tasks.py`) belirli bir sıra ile gerçekleştirir. Her ajanın çıktısı, bir sonraki ajanın girdisi (context) olarak kullanılır.
3.  **Sonuç Üretimi:** Son aşamada üretilen rapor hem dosya sistemi üzerinden kaydedilir hem de kullanıcıya web arayüzü üzerinden gösterilir.

## 🤖 Kullanılan Ajanlar ve Görevleri

Projede dört ana ajan bulunmaktadır:

### 1. Kıdemli Teknik İşe Alım Uzmanı (CV Parser Agent)
*   **Görevi:** CV'yi en ince ayrıntısına kadar analiz etmek.
*   **Ne İş Yapar?** Teknik becerileri (hard skills), sosyal becerileri (soft skills), eğitimi ve sertifikaları çıkarır. Ayrıca iş boşlukları veya belirsiz unvanlar gibi "kırmızı bayrakları" (red flags) tespit eder.

### 2. İşe Alım Yöneticisi Psikoloğu (Job Analyst Agent)
*   **Görevi:** İş ilanını iki katmanda analiz etmek.
*   **Ne İş Yapar?** Sadece yazılı olan gereksinimleri (TITLE, REQUIRED SKILLS) değil, satır aralarından okunabilen şirket kültürü ve gizli beklentileri de (startup kültürü, tempo vb.) çıkarır. ATS (Aday Takip Sistemi) için kritik anahtar kelimeleri belirler.

### 3. Kariyer Zekası Analisti (Gap Detector Agent)
*   **Görevi:** Adayın işe uygunluğunu veri odaklı olarak puanlamak.
*   **Ne İş Yapar?** CV ve iş ilanı verilerini karşılaştırarak "Güçlü Eşleşmeler", "Kısmi Eşleşmeler" ve "Kritik Eksiklikler" tabloları oluşturur. 0-100 arası bir puanlama yapar ve adaya "Hemen Başvur", "Önce Hazırlan" veya "Başvurma" şeklinde stratejik bir sonuç bildirir.

### 4. Uzman Kariyer Tercümanı (Translator Agent)
*   **Görevi:** İngilizce üretilen teknik raporu Türkçeye çevirmek.
*   **Ne İş Yapar?** "Hard Skills", "Gap Analysis" gibi teknik terimleri iş dünyasına uygun, profesyonel Türkçe karşılıklarıyla değiştirir. Raporun formatını (tablolar, emojiler, kalın metinler) bozmadan son derece akıcı ve okunabilir bir sonuç üretir.

## 📁 Proje Yapısı

*   `main.py`: FastAPI sunucusunu başlatan ve API yönlendirmelerini içeren dosya.
*   `agents.py`: Ajanların (Agent) kişiliklerini, rollerini ve araçlarını tanımlayan dosya.
*   `tasks.py`: Ajanların yapacağı görevlerin (Task) detaylarını ve senaryolarını içeren dosya.
*   `tools.py`: Dosya okuma (`file_reader_tool`) ve rapor kaydetme (`report_saver_tool`) gibi özel araçların bulunduğu dosya.
*   `config.py`: LLM (Yapay Zeka Modeli) ayarları ve çevre değişkenlerinin yönetildiği yer.

---
*Bu proje bir vize projesi kapsamında geliştirilmiştir.*
