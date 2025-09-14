"""Manual demo: chunking & embedding cache.
Çalıştır: python scripts/manual_chunking_demo.py
"""
import sys, os

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.chunking import tokenize_and_chunk
from app.core.embeddings import get_or_compute_embeddings

SAMPLE_TEXT = (
    "Yapay zekâ temelli öğretim asistanı, ders materyallerinin kapsamını ve öğretim performansını analiz eder. "
    "Bu sistem; kapsam, teslim ve pedagojik kalite metrikleri üretir. Amaç; eğitmenlere hızlı geri bildirim sağlamaktır. "
    "Örnek cümleler ekleyerek token sayısını artırıyoruz. Öğrencilerin dikkatini çeken örnekler ve açıklayıcı benzetmeler pedagojik kaliteyi yükseltir. "
    "Değerlendirme süreci sürekli iyileştirme döngüsü sağlar."
)


def main():
    chunks = tokenize_and_chunk(SAMPLE_TEXT, max_tokens=450, overlap=50, min_chunk_tokens=20)
    print(f"Chunk sayısı: {len(chunks)}")
    if chunks:
        print("İlk chunk token_count=", chunks[0]['token_count'])
    embedded = get_or_compute_embeddings(chunks, model='text-embedding-004', use_real=False)
    print(f"Embedding ekli chunk sayısı: {len(embedded)}")
    print("Örnek vektör uzunluğu:", len(embedded[0]['embedding']))


if __name__ == '__main__':
    main()
