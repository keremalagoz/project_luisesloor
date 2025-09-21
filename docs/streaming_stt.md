# Streaming STT (Deneysel)

Bu bileşen gerçek zamanlıya yakın (pseudo-streaming) transcript sağlar. Gerçek incremental model API'si olmadığı için tampon bazlı yeniden tam transcribe yaklaşımı kullanır.

## Dosya
`app/core/streaming_stt.py`

## Sınıf
```python
StreamingTranscriber(model_size='small', use_real=True, lang=None,
                     min_interval_sec=4.0, min_bytes=32000, max_buffer_bytes=2_000_000)
```

### feed(chunk: bytes) -> Optional[dict]
Belirtilen aralık (min_interval_sec) ve minimum byte eşiği (min_bytes) dolduğunda tam transcribe çağırır. Yeni metni önceki ile diff alır ve sadece eklenen kısmı `new_text` alanına koyar.

Dönen dict alanları:
- `full_text`: Tüm transcript
- `new_text`: Son emitten beri eklenen kısım
- `duration_seconds`
- `model`
- `cached`

### close() -> str
Akışı kapatır ve son full_text'i döndürür.

## UI Entegrasyonu
`main.py` mikrofon bölümünde "Canlı Streaming" checkbox açıldığında:
- Başlat: `StreamingTranscriber` örneği oluşturulur.
- Her frame döngüsünde kuyruktaki ses parçaları `feed` edilir.
- Partial çıktılar bir text_area'da gösterilir.
- Bitir: Kalan buffer işlenir, final transcript session state'e yazılır.

## Sınırlamalar
- Yeniden tam transcribe (O(N^2) değil ama maliyetli) — uzun kayıtlar için latency artar.
- Diff sadece ortak prefix üzerinden; silme / düzeltme algılamaz.
- Gerçek zamanlı kelime/segment zaman damgası güncellenmiyor (tam transcribe her seferinde yeni segment seti üretir).
- Audio formatı PCM ham akış; ileride WebRTC'den gelen frame'leri WAV konteynerine çevirme gerekebilir.

## Geliştirme Fikirleri
- Kayar pencere: Eski buffer kısmını transcript edilen metne göre kesip model girişini küçültme.
- Daha agresif interval adaptasyonu: Aktivite (ses enerjisi) düştüğünde beklemeyi artırma.
- Gerçek streaming API entegrasyonu (Whisper realtime, VAD + incremental).
- Partial segment highlight (yeni gelen kısmı renklendirme).
- WPM / filler gibi metrikleri canlı güncelleme (her partial sonrası incremental metrik hesaplama).

## Test
`tests/test_streaming_stt.py` fake modda küçük parçalar besleyerek en az bir partial çıktısı oluştuğunu doğrular.
