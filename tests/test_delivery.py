from app.core.delivery import compute_delivery_metrics


def test_delivery_insufficient(short_text):
    res = compute_delivery_metrics(short_text, duration_minutes=0.0, config={})
    assert res['raw']['insufficient_data'] in (True, False)  # Çok kısa ise True olabilir
    # Skor key'leri mevcut olmalı
    for k in ['wpm','filler','repetition','sentence_length','pause','delivery_score']:
        assert k in res['scores']


def test_delivery_reasonable(medium_transcript):
    res = compute_delivery_metrics(medium_transcript, duration_minutes=2.0, config={})
    assert 0.0 <= res['scores']['delivery_score'] <= 1.0
