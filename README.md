# AI Teaching Assistant (Streamlit)

AI destekli öğretmen asistanı: Ders materyallerini ve ders anlatımını analiz eder, kapsam ve teslim (delivery) metriklerine göre geri bildirim raporu üretir. Bu repo hackathon prototipi için Streamlit monolit mimarisiyle yapılandırılmıştır.

## Özellikler (Hedef)
- PDF/TXT yükleme ve metin çıkarma
- Embedding tabanlı içerik kapsam analizi (Gemini text-embedding-004)
- Konuşma → metin (OpenAI Whisper API)
- Teslim analizi: hız (WPM), duraklamalar, filler kelimeler, tekrar oranı
- Pedagojik analiz: açıklık, örnek yoğunluğu, etkileşim, dizgeleme, jargon yönetimi
- Skorlama: Overall = 0.5*Coverage + 0.3*Delivery + 0.2*Pedagogy
- Rapor: JSON + Markdown + PDF (ReportLab)
- İlerleme karşılaştırması (SQLite tabanlı, hafif)
 - Chunking: tiktoken ile 450 token max + 50 overlap (kısa <20 token parçalar elenir)
 - Embedding Cache: SHA256(model+chunk_text) ile disk cache (gelecek adım)

## Mimari
- UI/Orkestrasyon: Streamlit (tek uygulama)
- Çekirdek modüller: `app/core/*`
- Konfigürasyon: `config/settings.yaml`
- Örnek veri: `sample_data/`
- Dokümantasyon: `docs/`

## Kurulum (taslak)
1) Python 3.10+
2) Bağımlılıklar: `pip install -r requirements.txt`
3) API anahtarları: `.streamlit/secrets.toml` (bkz. `.streamlit/secrets.example.toml`)
4) Çalıştırma: `streamlit run main.py`

Not: Bu sürümde kod iskeleti boş bırakılmıştır. Gün 2 ile birlikte modüller doldurulacaktır.
 
### Modeller ve Parametreler
- LLM: Gemini 1.5 Flash (ücretsiz katman, hızlı yanıt)
- Embedding Modeli: text-embedding-004
- Chunk Parametreleri: max_tokens=450, overlap=50, min_chunk_tokens=20
- Cache Anahtarı: embedding_model + chunk_text (SHA256) -> tekrar hesaplamayı önler

### GPU (Plan B - PyTorch Whisper) Kurulumu
- CUDA 11.8 + RTX (ör. 4060) için:
	```bat
	pip install --upgrade pip
	pip install -r requirements.gpu-cu118.txt
	```
- İlk doğrulama:
	```bat
	python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
	```

## Lisans
MIT
