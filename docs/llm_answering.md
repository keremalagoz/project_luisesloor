# LLM Tabanlı Cevaplama

Bu belge RAG akışı üzerinde LLM (veya fake fallback) kullanarak cevap üretim sürecini açıklar.

## Modül
`app/core/llm.py`

## Ana Fonksiyonlar
- `build_prompt(question, context_chunks, max_context_chars)`
- `llm_complete(prompt, model, temperature)`
- `generate_llm_answer(question, retrieved, settings, temperature)`

## Akış
1. Kullanıcı chunk + embedding üretir (Adım 2).
2. RAG indeksi oluşturulur (Adım 8).
3. Sorgu ile similarity search → top-k retrieved.
4. `generate_llm_answer` top-k chunk metinlerini keserek bir prompt inşa eder.
5. Gemini API key varsa Gemini, yoksa OpenAI, ikisi de yoksa fake cevap döner.

## Prompt Formatı
```
Aşağıdaki içerik parçalarına dayanarak soruyu cevapla ...
[CHUNK c1]
<metin>
...
Soru: <kullanıcı sorusu>
Cevap (Türkçe, öz ve doğru):
```

## Fallback Stratejisi
Öncelik: Gemini → OpenAI → Fake (deterministik hash tabanlı mesaj).

## Konfig Parametreleri
`config/settings.yaml` içine default eklenir (kod tarafında):
```yaml
rag:
  max_chunks: 5
  max_context_chars: 4000
models:
  llm_model: gemini-pro
```

## Testler
`tests/test_llm_answer.py`:
- Prompt truncation
- Fake cevap üretimi (API anahtarı yok senaryosu)

## Geliştirme Fikirleri
- Hallucination azaltıcı direktifler (kaynak cümle ID referansı)
- Cevap uzunluk kontrolü (kelime limit)
- Çok dilli otomatik dil algılama ve prompt adaptasyonu
- Guardrail / moderasyon kontrolleri
- Cevap güven puanı (retrieval average similarity)

## Sınırlamalar
- Şu an LLM cevabı post-processing yapmıyor
- Citation highlight yok
- Streaming LLM çıktısı yok
