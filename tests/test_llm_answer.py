from app.core.llm import build_prompt, generate_llm_answer


def test_build_prompt_truncation():
    chunks = []
    # Toplamı aşacak birkaç chunk
    for i in range(5):
        chunks.append({'id': f'c{i+1}', 'text': 'x'*1200})
    prompt = build_prompt('Soru nedir?', chunks, max_context_chars=2500)
    # 2500 sınırını aşmamalı
    assert len(prompt) <= 2700  # başlık + soru ekleri küçük pay bırakıyoruz


def test_generate_llm_answer_fake():
    # API anahtarı yok varsayımı ile fake cevap gelir.
    retrieved = [
        {'id': 'c1', 'text': 'Makine öğrenmesi model eğitimi'},
        {'id': 'c2', 'text': 'Derin öğrenme çok katmanlı ağlar'}
    ]
    ans = generate_llm_answer('Derin öğrenme nedir?', retrieved, settings={'rag':{'max_chunks':2,'max_context_chars':1000}, 'models':{'llm_model':'gemini-pro'}})
    assert ans['mode'] == 'llm'
    assert 'answer' in ans
    assert ans['used_chunks'] == ['c1','c2'][:2]
