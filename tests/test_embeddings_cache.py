from app.core.embeddings import get_or_compute_embeddings, _hash_key  # type: ignore


def test_embedding_cache_reuse(tmp_path, monkeypatch):
    # Aynı metin tekrarlandığında cache devreye girmeli
    chunks = [ {'id': 'c1', 'text': 'Veri bilimi'}, {'id': 'c2', 'text': 'Veri bilimi'} ]
    emb1 = get_or_compute_embeddings(chunks, use_real=False)
    emb2 = get_or_compute_embeddings(chunks, use_real=False)
    # Aynı id'ler aynı vektöre sahip olmalı
    assert emb1[0]['embedding'] == emb2[0]['embedding']
    assert emb1[1]['embedding'] == emb2[1]['embedding']
