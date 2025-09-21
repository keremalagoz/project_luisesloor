"""Basit RAG (Retrieval Augmented Generation) yardımcıları.

Amaç: Var olan chunk + embedding listesini kullanarak kullanıcı soruları için
en alakalı parçaları bulmak ve basit extractive / heuristic cevap üretmek.

Gerçek LLM cevabı bu sürümde opsiyonel placeholder; ileride
Gemini / OpenAI entegrasyonu eklenebilir.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import re

from .embeddings import cosine_similarity, embed_texts


class VectorIndex:
    """In-memory basit vektör indeks.

    entries: List[{'id': str, 'text': str, 'embedding': List[float]}]
    """
    def __init__(self, entries: List[Dict[str, Any]]):
        self.entries = [e for e in entries if e.get('embedding')]
        self.dim = len(self.entries[0]['embedding']) if self.entries else 0

    def search(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        scored = []
        for e in self.entries:
            sim = cosine_similarity(query_vec, e['embedding'])
            scored.append((sim, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [dict(e[1], similarity=e[0]) for e in scored[:top_k]]


def build_index(chunks_with_embeddings: List[Dict[str, Any]]) -> VectorIndex:
    return VectorIndex(chunks_with_embeddings)


def _keyword_overlap_score(query: str, text: str) -> float:
    # Basit bag-of-words overlap oranı
    q_terms = set(t for t in re.findall(r"\w+", query.lower()) if len(t) > 2)
    if not q_terms:
        return 0.0
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    w_set = set(words)
    inter = len(q_terms & w_set)
    return inter / max(len(q_terms), 1)


def similarity_search(index: VectorIndex, query: str, model: str = 'text-embedding-004', use_real: bool = False, top_k: int = 5, hybrid_alpha: float = 1.0) -> List[Dict[str, Any]]:
    """Retrieval.
    hybrid_alpha: 1.0 => sadece dense; 0.0 => sadece keyword overlap; arası => harman
    """
    q_vec = embed_texts([query], model=model, use_real=use_real)[0]
    # Önce dense top-(top_k*3) çekip, sonra hibrid skorla yeniden sırala (küçük veri için basit yöntem)
    prelim = index.search(q_vec, top_k=max(top_k * 3, top_k))
    if hybrid_alpha >= 0.999:
        return prelim[:top_k]
    # Hibrid skorlama
    rescored = []
    for r in prelim:
        dense = float(r.get('similarity', 0.0))
        kw = _keyword_overlap_score(query, r.get('text', ''))
        score = hybrid_alpha * dense + (1.0 - hybrid_alpha) * kw
        new_r = dict(r)
        new_r['similarity'] = score
        rescored.append(new_r)
    rescored.sort(key=lambda x: x['similarity'], reverse=True)
    return rescored[:top_k]


def _extractive_answer(query: str, retrieved: List[Dict[str, Any]]) -> str:
    """Basit extractive cevap: en iyi chunk içinden cümle seçim heuristiği.
    - Sorgu kelimelerini içeren cümleleri puanlar
    - İlk 2 cümleyi birleştirir
    """
    if not retrieved:
        return "İlgili içerik bulunamadı."
    best = retrieved[0]['text']
    sentences = re.split(r'(?<=[.!?])\s+', best.strip())
    if len(sentences) <= 2:
        return best.strip()[:800]
    q_terms = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
    scored = []
    for s in sentences:
        lw = s.lower()
        score = sum(lw.count(t) for t in q_terms)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s for _, s in scored[:2] if s]
    if not top_sentences:
        return sentences[0][:800]
    ans = ' '.join(top_sentences)
    return ans[:800]


def generate_answer(
    query: str,
    retrieved: List[Dict[str, Any]],
    llm: bool = False,
) -> Dict[str, Any]:
    """Cevap üret.
    llm=False: heuristic extractive.
    llm=True: (şimdilik) aynı extractive + placeholder.
    """
    base_answer = _extractive_answer(query, retrieved)
    # Kaynak referansları ve basit güven skoru (benzerlik ortalaması)
    sources: List[Dict[str, Any]] = []
    if retrieved:
        for r in retrieved:
            sources.append({
                'id': r.get('id'),
                'similarity': float(r.get('similarity', 0.0)),
            })
        try:
            conf = sum(s['similarity'] for s in sources) / max(len(sources), 1)
        except Exception:
            conf = None
    else:
        conf = None

    if not llm:
        return {
            'answer': base_answer,
            'mode': 'extractive',
            'sources': sources,
            'confidence': conf,
        }
    # LLM placeholder
    return {
        'answer': base_answer + "\n\n(LLM cevabı placeholder - ileride geliştirilecek)",
        'mode': 'llm_placeholder',
        'sources': sources,
        'confidence': conf,
    }


__all__ = [
    'build_index',
    'similarity_search',
    'generate_answer',
    'VectorIndex'
]

# LLM entegrasyonu için yardımcı (opsiyonel)
def generate_llm_answer_via_index(index: VectorIndex, query: str, settings: Optional[Dict[str, Any]] = None, top_k: int = 5):  # type: ignore
    from .llm import generate_llm_answer as _gen_llm
    retrieved = similarity_search(index, query, use_real=False, top_k=top_k)
    return _gen_llm(query, retrieved, settings=settings)

__all__.append('generate_llm_answer_via_index')
