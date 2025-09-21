"""LLM cevaplama yardımcıları.

Gemini veya OpenAI desteği için soyut bir arayüz; API anahtarı yoksa
deterministik fake cevap üretir.

Fonksiyonlar:
 - build_prompt(question, context_chunks)
 - llm_complete(prompt, model, provider_auto, temperature)
 - generate_llm_answer(question, retrieved, settings)
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os, hashlib


def build_prompt(question: str, context_chunks: List[Dict[str, Any]], max_context_chars: int = 4000) -> str:
    ctx_parts = []
    total = 0
    for ch in context_chunks:
        t = ch.get('text','')
        if not t:
            continue
        if total + len(t) > max_context_chars:
            remain = max_context_chars - total
            if remain <= 0:
                break
            t = t[:remain]
        ctx_parts.append(f"[CHUNK {ch.get('id')}]\n{t}\n")
        total += len(t)
    ctx_block = "\n".join(ctx_parts)
    prompt = (
        "Aşağıdaki içerik parçalarına dayanarak soruyu cevapla. "
        "Yoksa 'Bu içerikte net cevap bulamadım' de.\n\n" +
        ctx_block +
        f"\nSoru: {question}\nCevap (Türkçe, öz ve doğru):"
    )
    return prompt


def _fake_llm(prompt: str) -> str:
    # Hash tabanlı deterministik kısa cevap.
    h = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:12]
    return f"(FAKE-LLM) Bu soru için özet üretilemedi; referans hash={h}."


def llm_complete(prompt: str, model: str = 'gpt-5-nano', temperature: float = 0.2) -> str:
    # Sağlayıcı seçimi:
    # - Model adı 'gpt' ile başlıyorsa veya ortamda OPENAI_API_KEY varsa OpenAI'ı deneriz.
    # - Başarısız olursa Gemini'a, o da yoksa fake cevaba düşeriz.
    openai_key = os.getenv('OPENAI_API_KEY')
    use_openai = (model.lower().startswith('gpt') or bool(openai_key)) and bool(openai_key)
    if use_openai:
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=openai_key)
            comp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=temperature,
            )
            return comp.choices[0].message.content  # type: ignore
        except Exception:
            pass
    # Gemini fallback
    gem_api = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gem_api:
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=gem_api)
            resp = genai.GenerativeModel(model).generate_content(prompt)
            if hasattr(resp, 'text'):
                return resp.text
            if isinstance(resp, dict):
                return str(resp)
        except Exception:
            pass
    return _fake_llm(prompt)


def generate_llm_answer(
    question: str,
    retrieved: List[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    rag_cfg = (settings or {}).get('rag') or {}
    max_chunks = rag_cfg.get('max_chunks', 5)
    max_context_chars = rag_cfg.get('max_context_chars', 4000)
    model = ((settings or {}).get('models') or {}).get('llm_model', 'gpt-5-nano')
    context_chunks = retrieved[:max_chunks]
    prompt = build_prompt(question, context_chunks, max_context_chars=max_context_chars)
    answer = llm_complete(prompt, model=model, temperature=temperature)
    return {
        'answer': answer,
        'model': model,
        'used_chunks': [c.get('id') for c in context_chunks],
        'prompt_chars': len(prompt),
        'mode': 'llm'
    }


__all__ = [
    'build_prompt',
    'llm_complete',
    'generate_llm_answer'
]
