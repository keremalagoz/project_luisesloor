"""Speech-to-Text (STT) yardımcı modülü.

Özellikler:
 - faster-whisper varsa gerçek transcribe, yoksa fake fallback
 - Mikro-cache: aynı audio bytes hash'i için tekrar model çalıştırmaz
 - Süre tahmini (pydub) + segment birleştirme
 - Dil otomatik tespit (whisper) veya kullanıcı override
 - Minimal arayüz: transcribe_audio(data: bytes, lang=None, model_size='small')
"""
from __future__ import annotations

import hashlib
import io
import os
from typing import Any, Dict, List, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

_TRANSCRIPT_CACHE: Dict[str, Dict[str, Any]] = {}
_MODEL_STORE: Dict[str, Any] = {}

try:  # pragma: no cover (import branch)
    from faster_whisper import WhisperModel  # type: ignore
    _FASTER_AVAILABLE = True
except Exception:
    _FASTER_AVAILABLE = False
    WhisperModel = None  # type: ignore
    logger.warning("faster-whisper import edilemedi; STT fake moda düşecek.")

try:  # pragma: no cover
    from pydub import AudioSegment  # type: ignore
    _PYDUB = True
except Exception:
    _PYDUB = False
    AudioSegment = None  # type: ignore


def compute_file_hash(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _estimate_duration(data: bytes) -> float:
    if not _PYDUB:
        return 0.0
    try:
        audio = AudioSegment.from_file(io.BytesIO(data))  # type: ignore
        return audio.duration_seconds
    except Exception:
        return 0.0


def _load_model(model_size: str = 'small'):
    if not _FASTER_AVAILABLE:
        return None
    if model_size in _MODEL_STORE:
        return _MODEL_STORE[model_size]
    # device / compute_type heuristics
    device = "cpu"
    compute_type = "int8"
    try:
        m = WhisperModel(model_size, device=device, compute_type=compute_type)  # type: ignore
        _MODEL_STORE[model_size] = m
        return m
    except Exception as e:
        logger.error("WhisperModel yüklenemedi: %s", e)
        return None


def _fake_result(duration: float, data_len: int) -> Dict[str, Any]:
    return {
        'text': f"FAKE TRANSCRIPT (len={data_len} bytes)",
        'segments': [],
        'duration_seconds': duration,
        'language': None,
        'model': 'fake',
        'cached': False,
    }


def transcribe_audio(data: bytes, *, lang: Optional[str] = None, model_size: str = 'small', use_real: bool = True) -> Dict[str, Any]:
    """Ses bytes -> transcript sözlüğü döndür.

    Dönen sözlük anahtarları:
      text, segments(list), duration_seconds, language, model, cached
    """
    file_hash = compute_file_hash(data)
    if file_hash in _TRANSCRIPT_CACHE:
        cached = _TRANSCRIPT_CACHE[file_hash].copy()
        cached['cached'] = True
        return cached

    duration = _estimate_duration(data)

    if not use_real or not _FASTER_AVAILABLE:
        res = _fake_result(duration, len(data))
        _TRANSCRIPT_CACHE[file_hash] = res
        return res

    model = _load_model(model_size)
    if model is None:
        res = _fake_result(duration, len(data))
        _TRANSCRIPT_CACHE[file_hash] = res
        return res

    try:
        segments_iter, info = model.transcribe(io.BytesIO(data), language=lang)  # type: ignore
        language = info.language if hasattr(info, 'language') else lang
        segments: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        for seg in segments_iter:
            seg_text = getattr(seg, 'text', '')
            start = float(getattr(seg, 'start', 0.0))
            end = float(getattr(seg, 'end', 0.0))
            if seg_text:
                full_text_parts.append(seg_text.strip())
            segments.append({
                'start': start,
                'end': end,
                'text': seg_text.strip(),
            })
        full_text = " ".join(full_text_parts).strip()
        if duration <= 0.0 and segments:
            duration = segments[-1]['end']
        result = {
            'text': full_text,
            'segments': segments,
            'duration_seconds': duration,
            'language': language,
            'model': f'faster-whisper-{model_size}',
            'cached': False,
        }
        _TRANSCRIPT_CACHE[file_hash] = result
        return result
    except Exception as e:
        logger.error("Transcribe başarısız: %s", e)
        res = _fake_result(duration, len(data))
        _TRANSCRIPT_CACHE[file_hash] = res
        return res


__all__ = [
    'transcribe_audio',
    'compute_file_hash',
]
