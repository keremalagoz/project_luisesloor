# Logging Yapılandırması

Bu projede merkezi logger `app/core/logger.py` içindedir ve config/env üzerinden yapılandırılabilir.

## Öncelik Sırası
1. `config/settings.yaml` içindeki `logging` bölümü (varsa)
2. Ortam değişkenleri
3. Varsayılanlar

## Desteklenen Ayarlar
- level (LOG_LEVEL): INFO | DEBUG | WARNING | ERROR | CRITICAL
- json (JSON_LOGS): 1/0 — JSON satırları (time, level, name, message)
- color (COLOR_LOGS): 1/0 — Konsolda seviye bazlı renk (JSON kapalıyken)
- file (LOG_FILE): Dosya yolu — RotatingFileHandler devreye girer
- max_bytes (LOG_MAX_BYTES): Döndürme eşiği (default 5MB)
- backup_count (LOG_BACKUP_COUNT): Dosya yedek sayısı (default 3)

## Örnek config/settings.yaml
```yaml
logging:
  level: INFO
  json: false
  color: true
  file: logs/app.log
  max_bytes: 5242880
  backup_count: 3
```

## Ortam Değişkeni Örnekleri (Windows cmd)
```bat
set LOG_LEVEL=DEBUG
set JSON_LOGS=1
set COLOR_LOGS=1
set LOG_FILE=%CD%\logs\app.log
set LOG_MAX_BYTES=10485760
set LOG_BACKUP_COUNT=5
```

## Kullanım
```python
from app.core.logger import get_logger
logger = get_logger()  # veya get_logger("my-module")
logger.info("Merhaba")
```

Notlar:
- JSON ve renkli konsol aynı anda aktif değildir; JSON aktifleştirilirse renk devre dışıdır.
- Dosya handler açılamazsa uygulama durmaz, konsola bir uyarı logu yazılır.
- İlk logger oluşturulduğunda config doğrulama çıktısı bir kez loglanır.
