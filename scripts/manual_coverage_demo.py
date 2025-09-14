"""Manual demo: coverage hesabı.
Çalıştır: python scripts/manual_coverage_demo.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.chunking import tokenize_and_chunk
from app.core.embeddings import get_or_compute_embeddings
from app.core.coverage import compute_coverage

SOURCE = (
    "Makine öğrenmesi giriş. Denetimli öğrenme örnekleri ve uygulama alanları. "
    "Temel kavram tanımlar ve sonuç bölümü."
)
TOPICS = """Giriş
Tanımlar
Örnekler
Uygulama Alanları
Sonuç
Regresyon"""  # 'Regresyon' muhtemelen missing


def main():
    chunks = tokenize_and_chunk(SOURCE, max_tokens=120, overlap=30)
    emb_chunks = get_or_compute_embeddings(chunks, model='text-embedding-004', use_real=False)
    cov = compute_coverage(emb_chunks, TOPICS, covered_thr=0.75, partial_thr=0.55)
    print(cov['summary'])
    for t in cov['topics']:
        print(t)


if __name__ == '__main__':
    main()
