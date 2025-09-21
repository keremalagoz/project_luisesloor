"""Basit (yarı) streaming STT katmanı.

Gerçek zamanlı model desteğimiz (faster-whisper incremental) olmadığından
heuristik bir yaklaşım uygularız:
 - Küçük PCM/audio parçaları bir buffer'da biriktirilir
 - Toplam süre (tahmini) veya byte eşiği aşıldığında tam transcribe çağrılır
 - Yeni transcribe metni öncekiyle diff alınarak 'partial' güncellemesi üretir

Bu yaklaşım düşük latency gerektiren durumlar için ideal değildir, ancak
demo amaçlı "canlı akıyor" hissi verir.
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
import time
import threading

from app.core.stt import transcribe_audio
from app.core.logger import get_logger

logger = get_logger(__name__)


class StreamingTranscriber:
    def __init__(
        self,
        *,
        model_size: str = 'small',
        use_real: bool = True,
        lang: Optional[str] = None,
        min_interval_sec: float = 4.0,
        min_bytes: int = 32_000,  # ~ birkaç sn PCM
        max_buffer_bytes: int = 2_000_000,
    ) -> None:
        self.model_size = model_size
        self.use_real = use_real
        self.lang = lang
        self.min_interval_sec = min_interval_sec
        self.min_bytes = min_bytes
        self.max_buffer_bytes = max_buffer_bytes
        self._buffer = bytearray()
        self._last_full_text = ""
        self._last_emit_time = 0.0
        self._lock = threading.Lock()
        self._closed = False

    def feed(self, chunk: bytes) -> Optional[Dict[str, Any]]:
        """Yeni audio bytes parçası besle.

        Geri dönüş:
          None -> henüz partial üretmedi
          dict -> {
             'full_text': str,
             'new_text': str (sadece yeni eklenen kısım),
             'duration_seconds': float,
             'model': str,
             'cached': bool
          }
        """
        if self._closed:
            return None
        now = time.time()
        with self._lock:
            self._buffer.extend(chunk)
            # Çok büyümüşse kırp (en eski kısmı at) - basit halka buffer
            if len(self._buffer) > self.max_buffer_bytes:
                overflow = len(self._buffer) - self.max_buffer_bytes
                del self._buffer[:overflow]
            should_emit = False
            if (now - self._last_emit_time) >= self.min_interval_sec and len(self._buffer) >= self.min_bytes:
                should_emit = True
            if not should_emit:
                return None
            data_copy = bytes(self._buffer)
        # Kilit dışında transcribe çağır
        res = transcribe_audio(data_copy, lang=self.lang, model_size=self.model_size, use_real=self.use_real)
        full_text = res.get('text') or ''
        if not full_text:
            return None
        # Diff hesapla (basit prefix match)
        prefix_len = 0
        for a, b in zip(full_text, self._last_full_text):
            if a == b:
                prefix_len += 1
            else:
                break
        new_text = full_text[prefix_len:]
        with self._lock:
            self._last_full_text = full_text
            self._last_emit_time = now
        return {
            'full_text': full_text,
            'new_text': new_text,
            'duration_seconds': res.get('duration_seconds'),
            'model': res.get('model'),
            'cached': res.get('cached'),
        }

    def close(self) -> str:
        """Akışı kapat ve son full text'i döndür."""
        with self._lock:
            self._closed = True
            return self._last_full_text


__all__ = ['StreamingTranscriber']
