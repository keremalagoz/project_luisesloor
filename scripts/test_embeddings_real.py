"""Gerçek embedding testi.
Kullanım: python scripts/test_embeddings_real.py
API key yoksa graceful skip.
"""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.embeddings import embed_texts  # noqa

SAMPLES = [
    "Bu bir deneme cümlesidir.",
    "Makine öğrenmesi gözetimli ve gözetimsiz yöntemleri kapsar.",
]

def main():
    use_real = bool(os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
    vecs = embed_texts(SAMPLES, use_real=use_real)
    print(f"Gerçek çağrı: {use_real}")
    for i, v in enumerate(vecs):
        print(i, len(v), 'ilk5=', v[:5])
    if use_real and any(len(v) < 8 for v in vecs):
        print("UYARI: Beklenenden kısa vektör boyutu.")

if __name__ == '__main__':
    main()
