from app.core.streaming_stt import StreamingTranscriber

# Bu test fake moda güvenebilir (use_real=False). Küçük chunk besleyip incremental çıktı almayı dener.

def test_streaming_partial_generation():
    st = StreamingTranscriber(use_real=False, min_interval_sec=0.0, min_bytes=10)
    # 3 parça besle, her seferinde partial dönmeli (fake transcript aynı kalıpta)
    parts = [b'aaaaabbbbb', b'cccccddddd', b'eeeefffff']
    outputs = []
    for p in parts:
        out = st.feed(p)
        if out:
            outputs.append(out)
    # En az bir partial üretmiş olmalı
    assert len(outputs) >= 1
    # full_text alanı string
    assert isinstance(outputs[-1]['full_text'], str)
    final = st.close()
    assert isinstance(final, str)
