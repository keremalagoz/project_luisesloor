# Config Doğrulama ve Logger

Bu doküman config yükleme, doğrulama ve loglama altyapısını açıklar.

## Dosya
- `app/core/config.py`: YAML okuma, environment genişletme, doğrulama.
- `app/core/logger.py`: Uygulama logger oluşturma ve doğrulama sonuçlarını ilk çağrıda loglama.

## Yükleme Akışı
1. `get_settings()` -> `config/settings.yaml` yüklenir (tek sefer cache).
2. `$(ENV_VAR)` pattern'leri ortam değişkenleri ile genişler. Örn: `$(DB_PATH)`.
3. `get_validation()` -> `validate_settings()` sonuçlarını döner.

## Doğrulama Kuralları
| Kural | Açıklama | Tür |
|-------|----------|-----|
| weights toplamı ~1 | coverage+delivery+pedagogy yaklaşık 1 (±0.01) | Error |
| delivery.weights =1 | Delivery alt ağırlıklar toplamı 1 | Error |
| pedagogy.weights =1 | Pedagogy alt ağırlıklar toplamı 1 | Error |
| covered > partial | similarity_thresholds için sıra | Error |
| embedding_model yok | models.embedding_model eksik | Warning |
| db_path dizini yok | Oluşturulamazsa | Error |
| db_path yazılabilir değil | Yazma izni yoksa | Warning |

`is_valid=False` ise uygulama sidebar'da uyarı gösterir.

## Logger
`get_logger()`:
- LOG_LEVEL ile seviye (varsayılan INFO)
- JSON_LOGS=1 -> JSON satır formatı
- İlk çağrıda validation sonuçlarını yazar.

## Testler
`tests/test_config_validation.py` senaryolar:
- Geçerli config
- Ağırlık hatası
- Threshold sırası hatası
- Embedding model eksik (warning)

## Genişletme Önerileri
- Pydantic şeması ile daha yapısal doğrulama
- Dinamik reload (dosya hash değişim tespiti)
- Kritik olmayan hataları otomatik düzeltme (örn. normalize ağırlıkları)

## Sık Karşılaşılan Hatalar
| Belirti | Olası Neden | Çözüm |
|---------|-------------|-------|
| weights toplamı 1.2 | Yanlış manuel düzenleme | Değerleri yeniden ölçekle |
| covered <= partial | Eşiklerin yeri karışmış | covered değerini yükselt veya partial'ı düşür |
| embedding_model uyarısı | Model adı boş | settings.yaml -> models.embedding_model ekle |
| db_path hatası | Dizin oluşturulamıyor | Yazma izni kontrol et, mutlak yol kullan |

## Örnek Minimal settings.yaml
```yaml
weights:
  coverage: 0.5
  delivery: 0.3
  pedagogy: 0.2
metrics:
  similarity_thresholds:
    covered: 0.78
    partial: 0.60
  delivery:
    weights:
      wpm: 0.2
      filler: 0.2
      repetition: 0.2
      sentence_length: 0.2
      pause: 0.2
  pedagogy:
    weights:
      examples: 0.2
      questions: 0.2
      signposting: 0.2
      definitions: 0.2
      summary: 0.2
models:
  embedding_model: text-embedding-004
app:
  db_path: data/app.sqlite
```

---
Bu altyapı ile yanlış veya eksik konfigürasyonlar erken aşamada saptanır ve kullanıcıya hem UI hem log üzerinden iletilir.
