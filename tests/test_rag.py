from app.core.rag import build_index, similarity_search, generate_answer


def _fake_chunks():
    # embedding boyutu 8 (fake embed) varsayımıyla kısa metinler
    texts = [
        "Makine öğrenmesi giriş dersinde temel kavramlar anlatılır.",
        "Denetimli öğrenme etiketli veri kullanır.",
        "Denetimsiz öğrenme veri yapısını keşfeder.",
        "Derin öğrenme çok katmanlı yapay sinir ağlarıdır.",
    ]
    # Fake embedding fonksiyonu embed_texts üzerinden giderdi, ama burada minimal yapı kuruyoruz
    # Testte embed_texts zaten deterministic fake üretecek; bu yüzden similarity_search çağrısı için tam yol izliyoruz.
    # Basitleştirme: embed_texts'i import et ve üret.
    from app.core.embeddings import embed_texts
    vecs = embed_texts(texts, use_real=False)
    chunks = []
    for i, (t, v) in enumerate(zip(texts, vecs), start=1):
        chunks.append({'id': f'c{i}', 'text': t, 'embedding': v})
    return chunks


def test_rag_build_and_search_basic():
    idx = build_index(_fake_chunks())
    res = similarity_search(idx, "derin öğrenme nedir", use_real=False, top_k=2)
    assert len(res) == 2
    # en benzer ilk chunk deep learning içermeli
    assert any('Derin öğrenme' in r['text'] for r in res)


def test_rag_answer_extractive():
    idx = build_index(_fake_chunks())
    res = similarity_search(idx, "denetimli öğrenme", use_real=False, top_k=3)
    ans = generate_answer("denetimli öğrenme", res)
    assert 'öğrenme' in ans['answer'].lower()
    assert ans['mode'] == 'extractive'
    # Yeni alanlar
    assert 'sources' in ans
    assert isinstance(ans['sources'], list)
    if ans['sources']:
        assert 'id' in ans['sources'][0]
        assert 'similarity' in ans['sources'][0]
    assert 'confidence' in ans


def test_rag_empty_results():
    idx = build_index([])  # boş indeks
    res = similarity_search(idx, "herhangi", use_real=False, top_k=3)
    # boş indeks -> sonuç yok
    assert res == []
    ans = generate_answer("herhangi", res)
    assert 'bulunamadı' in ans['answer']
