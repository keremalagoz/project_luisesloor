"""Merkezi config yükleme & doğrulama.

Özellikler:
 - YAML dosyasını yükler (varsayılan: config/settings.yaml)
 - $(ENV_VAR) pattern'lerini ortam değişkenleri ile genişletir
 - Temel tutarlılık kontrolleri (weights toplamı, threshold sırası vs.)
 - Tek sefer yükle-cache (idempotent erişim)
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import yaml
from typing import Any, Dict, Tuple, List, Optional

_SETTINGS_CACHE: Optional[Dict[str, Any]] = None
_VALIDATION_CACHE: Optional[Dict[str, Any]] = None

ENV_PATTERN = re.compile(r"\$\((?P<name>[A-Z0-9_]+)\)")


def _expand_env_values(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _expand_env_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_values(v) for v in obj]
    if isinstance(obj, str):
        def repl(m):
            name = m.group('name')
            return os.getenv(name, f"$({name})")
        return ENV_PATTERN.sub(repl, obj)
    return obj


def load_settings(path: str = 'config/settings.yaml', force: bool = False) -> Dict[str, Any]:
    """YAML config'i yükle ve environment referanslarını genişlet.
    force=True ile cache tazelenir.
    """
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is not None and not force:
        return _SETTINGS_CACHE
    # .env yükleyici (opsiyonel)
    try:
        from dotenv import load_dotenv  # type: ignore
        # Önce kök .env, sonra config/.env (ikisini de dene)
        load_dotenv()
        cfg_env = Path('config') / '.env'
        if cfg_env.exists():
            load_dotenv(dotenv_path=str(cfg_env), override=True)
    except Exception:
        pass
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config dosyası bulunamadı: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    data = _expand_env_values(data)
    # Varsayılan ek alanlar (eksikse doldur)
    defaults = {
        'rag': {
            'max_chunks': 5,
            'max_context_chars': 4000,
            'retrieval': {
                'default_hybrid_enabled': False,
                'default_alpha': 1.0,
                'default_top_k': 5,
            },
            'confidence': {
                'low': 0.5,
                'medium': 0.7,
            },
        },
        'models': {
            'llm_model': 'gpt-5-nano',
        },
        'stt': {
            'provider': 'openai',
            'openai_model': 'whisper-1'
        }
    }
    def merge(dst, src):
        for k,v in src.items():
            if isinstance(v, dict):
                node = dst.setdefault(k, {}) if isinstance(dst.get(k), dict) else {}
                if k not in dst or not isinstance(dst.get(k), dict):
                    dst[k] = {}
                merge(dst[k], v)
            else:
                dst.setdefault(k, v)
    merge(data, defaults)
    _SETTINGS_CACHE = data
    return data


def validate_settings(cfg: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Config sözlüğünü kontrol eder.

    Dönen: (is_valid, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # weights toplamı
    weights = (cfg.get('weights') or {})
    if weights:
        total = sum(v for v in weights.values() if isinstance(v, (int, float)))
        if not (0.99 <= total <= 1.01):
            errors.append(f"'weights' toplamı ~1 olmalı (şu an {total:.3f}).")

    # delivery weights
    delivery_weights = (((cfg.get('metrics') or {}).get('delivery') or {}).get('weights')) or {}
    if delivery_weights:
        d_total = sum(v for v in delivery_weights.values() if isinstance(v, (int, float)))
        if abs(d_total - 1.0) > 0.01:
            errors.append(f"delivery.weights toplamı 1 olmalı (şu an {d_total:.3f}).")

    # pedagogy weights
    pedagogy_weights = (((cfg.get('metrics') or {}).get('pedagogy') or {}).get('weights')) or {}
    if pedagogy_weights:
        p_total = sum(v for v in pedagogy_weights.values() if isinstance(v, (int, float)))
        if abs(p_total - 1.0) > 0.01:
            errors.append(f"pedagogy.weights toplamı 1 olmalı (şu an {p_total:.3f}).")

    # similarity thresholds
    sim = ((cfg.get('metrics') or {}).get('similarity_thresholds')) or {}
    covered = sim.get('covered')
    partial = sim.get('partial')
    if isinstance(covered, (int, float)) and isinstance(partial, (int, float)):
        if covered <= partial:
            errors.append("similarity_thresholds.covered > partial şartı sağlanmalı.")

    # embedding model
    emb_model = (cfg.get('models') or {}).get('embedding_model')
    if not emb_model:
        warnings.append("models.embedding_model tanımlı değil.")

    # db_path yazılabilirlik
    app_cfg = cfg.get('app') or {}
    db_path = app_cfg.get('db_path')
    if db_path:
        parent = os.path.dirname(db_path) or '.'
        if not os.path.exists(parent):
            try:
                os.makedirs(parent, exist_ok=True)
            except Exception:
                errors.append(f"db_path dizini oluşturulamadı: {parent}")
        else:
            if not os.access(parent, os.W_OK):
                warnings.append(f"db_path dizinine yazma izni olmayabilir: {parent}")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def get_settings(force: bool = False) -> Dict[str, Any]:
    return load_settings(force=force)


def get_validation(force: bool = False) -> Dict[str, Any]:
    global _VALIDATION_CACHE
    if _VALIDATION_CACHE is not None and not force:
        return _VALIDATION_CACHE
    cfg = get_settings(force=force)
    is_valid, errors, warnings = validate_settings(cfg)
    _VALIDATION_CACHE = {
        'is_valid': is_valid,
        'errors': errors,
        'warnings': warnings,
    }
    return _VALIDATION_CACHE


__all__ = [
    'get_settings',
    'get_validation',
    'validate_settings',
    'load_settings',
]
