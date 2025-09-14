# STT (Speech-to-Text) Modülü

Bu doküman `app/core/stt.py` modülünün kullanımını ve tasarım kararlarını açıklar.

## Amaç
Yüklenen ses dosyaları veya mikrofon kaydı üzerinden transkript üretip Delivery & Pedagogy analizlerine beslemek.

## Özellikler
- faster-whisper varsa gerçek model ile inference, yoksa fake fallback.
- SHA256 hash tabanlı in-memory cache (tekrar işlenen aynı dosyada hız).
- Süre tahmini (pydub) ve segment çıktısı.
- Dil otomatik tespit (model destekliyorsa) veya manuel override parametresi.
- Mikrofon kaydı (WebRTC) → kayıt bitince batch transcribe (streaming partial sonraki iterasyon).

## Ana Fonksiyon
```python
transcribe_audio(data: bytes, *, lang: str|None=None, model_size: str='small', use_real: bool=True) -> dict
```
Dönen sözlük:
```jsonc
{
  "text": "...",          // Tam transkript
  "segments": [            // Segment listesi
    {"start": 0.0, "end": 3.2, "text": "..."}
  ],
  "duration_seconds": 12.34,
  "language": "en",
  "model": "faster-whisper-small" | "fake",
  "cached": false
}
```

## Fake Mode
`use_real=False` veya faster-whisper import hatası → `model: fake` ve placeholder text.
Bu, demo / offline ortam için hızlıdır.

## Cache Davranışı
İlk çağrı: `cached=False`
Aynı bytes (hash) tekrar: `cached=True` ve önceki sözlük kopyası döner.

## Mikrofon Kaydı Akışı
1. Kullanıcı "Kaydı Başlat" → WebRTC audio frame callback PCM verileri queue'ya yazar.
2. "Kaydı Bitir" → queue boşaltılır, tüm bytes birleştirilir.
3. `transcribe_audio` çağrısı yapılıp sonuç transcript alanına kaydedilir.
4. Süre hesaplanır ve `auto_duration_min` güncellenir.

## Sınırlamalar
- Streaming partial transcription henüz yok (Naif / segment overlap sonraki sprint).
- Uzun kayıtlar CPU süresi yaratabilir (small model > tiny tercih edilirse daha yavaş).
- Cache sadece memory (uygulama yeniden başlatılınca kaybolur).

## Genişletme Önerileri
- Disk tabanlı cache (hash -> JSON + segment pickle).
- Streaming (segment overlap veya harici API provider).
- Dil otomatik tespit başarısız olursa fallback heuristics.
- Noise reduction / VAD pre-processing.

## Testler
`tests/test_stt_fake.py`:
- Fake mode temel çıktılar
- Cache reuse doğrulama
- Hash stabilitesi

## Örnek Kullanım
```python
from app.core.stt import transcribe_audio
with open("sample.wav", "rb") as f:
    data = f.read()
res = transcribe_audio(data, use_real=True, model_size='small')
print(res['text'])
```

---
Bu modül MVP gereksinimlerini kapsar; gerçek zamanlı (partial) transcript için temel zemin hazırlanmıştır.
