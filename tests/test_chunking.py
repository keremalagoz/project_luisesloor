from app.core.chunking import tokenize_and_chunk, validate_overlap


def test_chunking_basic():
    text = "Cümle bir. Cümle iki. Cümle üç. Cümle dört."
    chunks = tokenize_and_chunk(text, max_tokens=50, overlap=5, min_chunk_tokens=5, store_tokens=True)
    assert chunks, "Chunk listesi boş olmamalı"
    assert all(c['token_count'] >= 5 for c in chunks), "Min token filtresi çalışmıyor"
    assert validate_overlap(chunks, 5), "Overlap doğrulaması başarısız"


def test_chunking_hard_split():
    # Tek cümle max_tokens'tan büyükse hard split
    long_sentence = "Kelime " * 120  # token ~ kelime varsayımı kaba
    text = long_sentence + ". Kısa cümle."
    chunks = tokenize_and_chunk(text, max_tokens=40, overlap=0, min_chunk_tokens=5)
    # Hard split en az 2 chunk üretmeli
    assert len(chunks) >= 2
