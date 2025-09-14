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
from typing import Dict, Any

_INITIALIZED_LOGGERS = set()
_VALIDATION_LOGGED = False


def _json_formatter(record: logging.LogRecord) -> str:
    data = {
        "level": record.levelname,
        "name": record.name,
        "message": record.getMessage(),
        "time": getattr(record, 'asctime', None),
    }
    if record.exc_info:
        data["exc_info"] = True
    return json.dumps(data, ensure_ascii=False)


class _JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        return _json_formatter(record)


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if name not in _INITIALIZED_LOGGERS:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            logger.setLevel(getattr(logging, level))
        except AttributeError:
            logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        if os.getenv("JSON_LOGS") == "1":
            handler.setFormatter(_JSONLogFormatter())
        else:
            fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
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
