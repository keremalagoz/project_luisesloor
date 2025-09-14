from app.core.stt import transcribe_audio, compute_file_hash

def test_fake_mode_basic():
    data = b"abcdefg" * 100
    res = transcribe_audio(data, use_real=False)
    assert 'text' in res
    assert res['model'] == 'fake'
    assert res['cached'] is False

def test_cache_reuse():
    data = b"xyz123" * 200
    r1 = transcribe_audio(data, use_real=False)
    r2 = transcribe_audio(data, use_real=False)
    assert r2['cached'] is True
    assert r1['text'] == r2['text']

def test_hash_stability():
    data = b"hash-me-please"
    h1 = compute_file_hash(data)
    h2 = compute_file_hash(data)
    assert h1 == h2
