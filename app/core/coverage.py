"""Coverage hesaplama modülü.

Adımlar:
1. Topic satırlarını normalize et ve boş olanları at.
2. Topic embedding'lerini (fake veya gerçek) hesapla (embedding cache zaten metin bazlı çalışıyor).
3. Chunk embedding'leri ile topic embedding'leri arasında cosine matrisi oluştur.
4. Her topic için en yüksek skor ve hangi chunk'ta olduğu.
5. Skora göre sınıflandırma (covered / partial / missing).
6. Özet istatistik ve coverage ratio.
"""
from __future__ import annotations
from typing import List, Dict, Tuple
from app.core.embeddings import get_or_compute_embeddings, cosine_similarity, embed_texts


def prepare_topics(raw: str) -> List[str]:
    lines = [l.strip() for l in raw.splitlines()]
    topics = [l for l in lines if l]
    # Tekrarlı satırları korumak mı? Şimdilik benzersiz yapalım:
    uniq = []
    seen = set()
    for t in topics:
        if t.lower() not in seen:
            seen.add(t.lower())
            uniq.append(t)
    return uniq


def embed_topics(topics: List[str], model: str = 'text-embedding-004', use_real: bool = False) -> List[Dict]:
    # get_or_compute_embeddings chunk formatı bekliyor; adaptör yapalım
    temp_chunks = [
        {'id': f't{i+1}', 'text': t, 'token_count': 0, 'start_token': 0, 'end_token': 0}
        for i, t in enumerate(topics)
    ]
    embedded = get_or_compute_embeddings(temp_chunks, model=model, use_real=use_real)
    # Sadece (topic, embedding) döndürelim
    return [{'topic': t['text'], 'embedding': t['embedding']} for t in embedded]


def similarity_matrix(chunk_embeddings: List[Dict], topic_embeddings: List[Dict]) -> List[List[float]]:
    matrix: List[List[float]] = []
    for ch in chunk_embeddings:
        row = []
        for tp in topic_embeddings:
            row.append(cosine_similarity(ch['embedding'], tp['embedding']))
        matrix.append(row)
    return matrix


def classify(score: float, covered_thr: float, partial_thr: float) -> str:
    if score >= covered_thr:
        return 'covered'
    if score >= partial_thr:
        return 'partial'
    return 'missing'


def compute_coverage(
    embedded_chunks: List[Dict],
    raw_topics: str,
    covered_thr: float = 0.78,
    partial_thr: float = 0.60,
    model: str = 'text-embedding-004',
    use_real: bool = False,
) -> Dict:
    topics = prepare_topics(raw_topics)
    if not topics:
        return {'topics': [], 'summary': {'covered':0,'partial':0,'missing':0,'coverage_ratio':0.0}}
    topic_embs = embed_topics(topics, model=model, use_real=use_real)
    # Matrix: n_chunks x n_topics
    if not embedded_chunks:
        # Hepsi missing
        results = [{'topic': t['topic'], 'status': 'missing', 'best_score': 0.0, 'best_chunk_id': None} for t in topic_embs]
    else:
        matrix = similarity_matrix(embedded_chunks, topic_embs)
        # topic sütunları üzerinden max bul
        results = []
        for j, tp in enumerate(topic_embs):
            # j'inci topic için tüm chunk skorları
            col_scores = [matrix[i][j] for i in range(len(embedded_chunks))]
            best_score = max(col_scores)
            best_idx = col_scores.index(best_score)
            best_chunk_id = embedded_chunks[best_idx]['id']
            status = classify(best_score, covered_thr, partial_thr)
            results.append({
                'topic': tp['topic'],
                'status': status,
                'best_score': best_score,
                'best_chunk_id': best_chunk_id,
            })
    summary = {
        'covered': sum(1 for r in results if r['status']=='covered'),
        'partial': sum(1 for r in results if r['status']=='partial'),
        'missing': sum(1 for r in results if r['status']=='missing'),
    }
    total = len(results) or 1
    summary['coverage_ratio'] = summary['covered'] / total
    return {'topics': results, 'summary': summary}

__all__ = [
    'compute_coverage',
    'prepare_topics'
]
