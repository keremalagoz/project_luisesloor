# RAG (Retrieval Augmented Generation)

Bu modül ders materyali chunk + embedding verisinden soru-cevap üretmeyi sağlar.

## Amaç
Kullanıcı metin hakkında doğal dil soruları sorduğunda en alakalı bölümleri getirip basit bir extractive cevap sunmak.

## Modül Konumu
`app/core/rag.py`

## Ana Bileşenler
- `VectorIndex`: Bellekte tutulan basit vektör indeks (liste taraması + cosine similarity).
- `build_index(chunks_with_embeddings) -> VectorIndex`
- `similarity_search(index, query, model, use_real, top_k)`
  - Not: `hybrid_alpha` parametresi ile hibrit (dense + keyword overlap) skorlaması desteklenir. 1.0 sadece dense, 0.0 sadece keyword.
- `generate_answer(query, retrieved, llm=False)`

## Veri Formatı
Chunk (embedding sonrası):
```json
{
  "id": "c12",
  "text": "...chunk metni...",
  "embedding": [0.12, -0.03, ...]
}
```

`generate_answer` dönüşü (özet):
```json
{
  "answer": "...",
  "mode": "extractive | llm_placeholder",
  "sources": [
    {"id": "c1", "similarity": 0.83},
    {"id": "c5", "similarity": 0.78}
  ],
  "confidence": 0.805
}
```

## Akış
1. Adım 2'de chunk + embedding üret.
2. RAG için "İndeksi Oluştur" butonuna bas → `VectorIndex` bellekte.
3. Soru yaz → `similarity_search` top-k chunk.
4. `generate_answer` first chunk cümlelerine basit scoring ile kısa cevap döndürür.
5. (Opsiyonel) LLM modunda placeholder şu an extractive sonucu + not ekler.
6. (Opsiyonel) Hibrit Retrieval: UI’de “Hibrit Retrieval” seçilerek `alpha` ile harman ağırlığı ayarlanır.

## Extractive Heuristik
- En iyi chunk = en yüksek cosine similarity.
- Cümlelere böl → Sorgu kelimelerinin frekansına göre puanla.
- En iyi 2 cümleyi birleştir, 800 karakterde kes.
- Hiç cümle yoksa chunk ham metnini döndür.

## Sınırlamalar
- Vektör araması O(N) lineer (küçük veri setleri için yeterli).
- Gerçek LLM cevabı yok; placeholder.
- Çok dilli sorgularda embedding modeli aynı değilse kalite düşer.
- Cümle bölme regex basit; noktalama varyasyonları için kusurlu olabilir.

## Geliştirme Fikirleri
- ANN kütüphanesi (FAISS / hnswlib) entegrasyonu.
- Cevap sentezi için LLM (context window içine top-k chunk enjekte).
- Kaynak snippet highlight (cevapta referans işaretleme).
- Chunk scorlarında *recency* veya *section weight* gibi meta kullanımı.
- Stopword filtreli TF-IDF hibrit skorlama (dense + sparse fusion).

## Testler
`tests/test_rag.py`:
- Temel arama ilk sonuç doğrulama.
- Extractive mod cevabı.
- Boş indeks fallback.

## Performans
## Konfigürasyon Varsayılanları
`config/settings.yaml` içinde `rag` bölümüyle varsayılanlar ayarlanabilir. Eksikse aşağıdaki defaults kullanılır:

```yaml
rag:
  max_chunks: 5
  max_context_chars: 4000
  retrieval:
    default_hybrid_enabled: false
    default_alpha: 1.0
    default_top_k: 5
  confidence:
    low: 0.5
    medium: 0.7
```

UI, Adım 8’de bu varsayılanları okur ve Hibrit/Alpha/Top-K varsayılanlarını uygular. Confidence, low/medium eşiklerine göre rozetlenir.
Küçük veri (<= birkaç yüz chunk) için lineer arama yeterli (< birkaç ms). Daha büyük veri için FAISS önerilir.
