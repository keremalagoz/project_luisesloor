"""Transkript modülü (yer tutucu)
- OpenAI Whisper API ile konuşma → metin
- Zaman damgaları ve sessizlik analizi için segment verisi
- Plan B: PyTorch + openai/whisper (GPU) yerel çalıştırma
"""

from typing import Any, Dict, List


def transcribe(audio_path: str, provider: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Unified transcription interface.
    Returns: { 'text': str, 'segments': List[{start: float, end: float, text: str}], 'duration_sec': float }
    """
    if provider == "openai":
        return _transcribe_openai(audio_path)

    if provider == "local":
        backend = settings.get("models", {}).get("stt_local_backend", "torch")
        if backend == "torch":
            return _transcribe_torch(audio_path, settings)
        else:
            raise NotImplementedError("Only 'torch' backend stub is prepared")

    raise ValueError(f"Unknown STT provider: {provider}")


def _transcribe_openai(audio_path: str) -> Dict[str, Any]:
    """OpenAI Whisper API yolunu bağlamak için iskelet; secrets'tan anahtar okur."""
    import os
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else OpenAI()

    with open(audio_path, "rb") as f:
        # Not: OpenAI'nın yeni Audio transcriptions endpoint'ine göre
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json"
        )

    text = transcript.text if hasattr(transcript, "text") else ""
    segments = []
    # verbose_json segmentleri döndürürse uyarlayabiliriz; şimdilik boş tutuyoruz
    duration = 0.0
    return {"text": text, "segments": segments, "duration_sec": duration}


def _transcribe_torch(audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Local PyTorch Whisper GPU/CPU fallback stub.
    Uses openai-whisper with torch.cuda if available and requested.
    """
    import torch  # type: ignore
    import whisper  # openai-whisper

    device_pref = settings.get("models", {}).get("stt_local_device", "cuda")
    language = settings.get("models", {}).get("stt_local_language", "tr")
    model_name = settings.get("models", {}).get("stt_local_model", "medium")
    beam_size = int(settings.get("models", {}).get("stt_local_beam_size", 1))

    use_cuda = device_pref == "cuda" and torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"

    print(f"[transcript] Using device: {device}, model: {model_name}")
    model = whisper.load_model(model_name, device=device)

    fp16 = use_cuda
    result = model.transcribe(audio_path, language=language, fp16=fp16, beam_size=beam_size)

    text = result.get("text", "")
    segments_raw = result.get("segments", []) or []
    segments: List[Dict[str, Any]] = []
    for s in segments_raw:
        segments.append({
            "start": float(s.get("start", 0.0)),
            "end": float(s.get("end", 0.0)),
            "text": str(s.get("text", ""))
        })

    duration = 0.0
    if segments:
        duration = max((seg["end"] for seg in segments), default=0.0)

    return {"text": text, "segments": segments, "duration_sec": duration}
