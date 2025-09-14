from app.core.pedagogy import compute_pedagogy_metrics


def test_pedagogy_insufficient():
    txt = "Kısa cümle. İki cümle."  # çok az cümle
    res = compute_pedagogy_metrics(txt, config={'min_sentences': 5})
    assert res['raw']['insufficient_data'] is True
    assert res['scores']['pedagogy_score'] == 0.0


def test_pedagogy_balance():
    # Dengeyi tetikleyebilecek metin (heuristik)
    txt = (
        "Örnek olarak bir sayı verelim. Bu tanım önemlidir. Peki neden böyle? "
        "Şimdi adım adım ilerleyeceğiz. Sonuç olarak özetleyelim. "
        "Bir başka örnek daha. Neden sorusunu tekrar soralım."
    )
    res = compute_pedagogy_metrics(txt, config={'min_sentences': 3})
    assert 0.0 <= res['scores']['pedagogy_score'] <= 1.0
