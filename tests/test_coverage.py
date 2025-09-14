from app.core.embeddings import get_or_compute_embeddings
from app.core.coverage import compute_coverage


def test_coverage_classification():
    # Basit iki topic; biri geçecek diğeri düşük similarity
    chunks = [
        {'id': 'c1', 'text': 'Makine öğrenmesi modelleri veri ile eğitilir.'},
        {'id': 'c2', 'text': 'Regresyon ve sınıflandırma gözetimli tekniklerdir.'},
    ]
    embedded = get_or_compute_embeddings(chunks, model='text-embedding-004', use_real=False)
    topics = "Makine öğrenmesi\nGörüntü işleme"  # ikinci eksik kalır
    cov = compute_coverage(embedded, topics, covered_thr=0.75, partial_thr=0.50, model='text-embedding-004', use_real=False)
    statuses = {t['topic']: t['status'] for t in cov['topics']}
    assert 'Makine öğrenmesi' in statuses
    assert 'Görüntü işleme' in statuses
    # En az bir missing veya partial olmalı
    assert any(s != 'covered' for s in statuses.values())
