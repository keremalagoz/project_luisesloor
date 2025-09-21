"""Uygulama logger yardımcıları.

Özellikler:
 - get_logger(name): tekil instance (duplicate handler engelleme)
 - LOG_LEVEL env ile seviye kontrolü (default INFO)
 - JSON_LOGS=1 ise basit JSON line format
 - Varsayılan format: zaman | seviye | isim | mesaj
 - İlk çağrıda config doğrulama sonuçlarını (uygunsa) loglar
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime

_INITIALIZED_LOGGERS = set()
_VALIDATION_LOGGED = False


def _json_formatter(record: logging.LogRecord) -> str:
    # ISO8601 UTC timestamp
    ts = datetime.utcfromtimestamp(record.created).isoformat(timespec='seconds') + 'Z'
    data = {
        "level": record.levelname,
        "name": record.name,
        "message": record.getMessage(),
        "time": ts,
    }
    if record.exc_info:
        data["exc_info"] = True
    return json.dumps(data, ensure_ascii=False)


class _JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        return _json_formatter(record)


class _ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\x1b[36m',      # Cyan
        'INFO': '\x1b[32m',       # Green
        'WARNING': '\x1b[33m',    # Yellow
        'ERROR': '\x1b[31m',      # Red
        'CRITICAL': '\x1b[41m',   # Red background
    }
    RESET = '\x1b[0m'

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        base = super().format(record)
        color = self.COLORS.get(record.levelname)
        if not color:
            return base
        # Seviye adını renklendir
        return base.replace(record.levelname, f"{color}{record.levelname}{self.RESET}")


def _coerce_int(val: Optional[str], default: int) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default


def get_logger(name: str = "app") -> logging.Logger:
    """Uygulama logger'ı döndürür.

    Yapılandırma önceliği:
      1) config.get_settings()['logging'] (varsa)
      2) Ortam değişkenleri
      3) Varsayılanlar
    Desteklenen env/config anahtarları:
      - level (LOG_LEVEL)
      - json (JSON_LOGS=1)
      - color (COLOR_LOGS=1; yalnız JSON kapalıyken)
      - file (LOG_FILE)
      - max_bytes (LOG_MAX_BYTES)
      - backup_count (LOG_BACKUP_COUNT)
    """
    logger = logging.getLogger(name)
    if name not in _INITIALIZED_LOGGERS:
        # Config oku (opsiyonel)
        cfg_logging: Dict[str, Any] = {}
        try:
            from .config import get_settings  # lokal import: dairesel bağımlılığı önle
            cfg = get_settings()
            cfg_logging = (cfg.get('logging') or {}) if isinstance(cfg, dict) else {}
        except Exception:
            cfg_logging = {}

        # Level
        level_str = (cfg_logging.get('level') or os.getenv("LOG_LEVEL", "INFO")).upper()
        try:
            logger.setLevel(getattr(logging, level_str))
        except AttributeError:
            logger.setLevel(logging.INFO)

        # Konsol handler
        console_handler = logging.StreamHandler()
        use_json = bool(int(str(cfg_logging.get('json') if cfg_logging.get('json') is not None else os.getenv("JSON_LOGS", "0")).strip() or '0'))
        use_color = bool(int(str(cfg_logging.get('color') if cfg_logging.get('color') is not None else os.getenv("COLOR_LOGS", "0")).strip() or '0'))
        if use_json:
            console_handler.setFormatter(_JSONLogFormatter())
        else:
            fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            if use_color:
                console_handler.setFormatter(_ColorFormatter(fmt))
            else:
                console_handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(console_handler)

        # Dosya handler (opsiyonel)
        log_file = str(cfg_logging.get('file') or os.getenv("LOG_FILE") or '').strip()
        if log_file:
            max_bytes = _coerce_int(os.getenv("LOG_MAX_BYTES"), 5 * 1024 * 1024)
            max_bytes = int(cfg_logging.get('max_bytes', max_bytes))
            backup_count = _coerce_int(os.getenv("LOG_BACKUP_COUNT"), 3)
            backup_count = int(cfg_logging.get('backup_count', backup_count))
            try:
                fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
                if use_json:
                    fh.setFormatter(_JSONLogFormatter())
                else:
                    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    fh.setFormatter(logging.Formatter(fmt))
                logger.addHandler(fh)
            except Exception as e:
                # Dosya handler kurulamazsa konsola uyarı yaz, uygulamayı durdurma
                logger.warning("Dosya log handler başlatılamadı: %s", e)

        logger.propagate = False
        _INITIALIZED_LOGGERS.add(name)
        _maybe_log_validation(logger)
    return logger


def _maybe_log_validation(logger: logging.Logger) -> None:
    global _VALIDATION_LOGGED
    if _VALIDATION_LOGGED:
        return
    try:
        from .config import get_validation
        v = get_validation()
        if v["errors"]:
            logger.error("Config validation errors: %s", v["errors"])
        if v["warnings"]:
            logger.warning("Config validation warnings: %s", v["warnings"])
        logger.info("Config validation status: valid=%s", v["is_valid"])
    except Exception as e:  # pragma: no cover
        logger.debug("Validation loglama başarısız: %s", e)
    _VALIDATION_LOGGED = True


__all__ = ["get_logger"]
