# Mimari Özeti

- Tek uygulama (monolit): Streamlit UI + orkestrasyon
- Çekirdek modüller (`app/core`): ingestion, embeddings, transcript, delivery, pedagogy, scoring, report, progress
- Konfigürasyon (`config/settings.yaml`): eşikler, model adları, ağırlıklar
- Depolama: SQLite (rapor geçmişi), dosya sistemi (uploadlar)
- Sağlayıcılar:
  - Embedding/LLM: Gemini (text-embedding-004, 1.5 Flash)
  - STT: OpenAI Whisper API
- Dağıtım: Streamlit Cloud veya Railway (Python barındırma)

Diyagram (yüksek seviye):

Uploads → Ingestion → Chunk+Embed → Transcript(Whisper) → Coverage+Delivery+Pedagogy → Scoring → Report(JSON/MD/PDF) → Progress(Store)
