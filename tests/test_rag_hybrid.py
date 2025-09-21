from app.core.rag import build_index, similarity_search
from app.core.embeddings import embed_texts


def _chunks_texts():
    return [
        "Makine öğrenmesi giriş dersinde temel kavramlar anlatılır.",
        "Denetimli öğrenme etiketli veri kullanır.",
        "Denetimsiz öğrenme veri yapısını keşfeder.",
        "Derin öğrenme çok katmanlı yapay sinir ağlarıdır.",
        "Bu bölüm matematiksel altyapıyı içerir: vektör, matris, türev.",
    ]


def _fake_chunks():
    vecs = embed_texts(_chunks_texts(), use_real=False)
    chunks = []
    for i, (t, v) in enumerate(zip(_chunks_texts(), vecs), start=1):
        chunks.append({'id': f'c{i}', 'text': t, 'embedding': v})
    return chunks


essay_query = "makine öğrenmesi ve kavramlar"
keyword_query = "vektör matris türev"


def test_hybrid_vs_dense_topk():
    idx = build_index(_fake_chunks())
    # Dense-only
    dense = similarity_search(idx, essay_query, use_real=False, top_k=3, hybrid_alpha=1.0)
    # Hybrid with some keyword weight
    hybrid = similarity_search(idx, essay_query, use_real=False, top_k=3, hybrid_alpha=0.5)
    assert len(dense) == 3 and len(hybrid) == 3
    # Sıralama farklı olabilir, ama skorlama alanı mevcut
    assert all('similarity' in r for r in hybrid)


def test_keyword_dominant_case():
    idx = build_index(_fake_chunks())
    # Keyword ağırlığı yüksek olunca matematik metni öne çıkmalı
    hy = similarity_search(idx, keyword_query, use_real=False, top_k=2, hybrid_alpha=0.0)
    assert any('matematik' in r['text'] or 'vektör' in r['text'] for r in hy)
