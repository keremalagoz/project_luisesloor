"""Manual demo: pedagogy metrikleri.
Çalıştır: python scripts/manual_pedagogy_demo.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.pedagogy import compute_pedagogy_metrics  # noqa

SCENARIOS = {
    "dengeli": "Önce veri kavramını tanımlayalım. Veri nedir? Örneğin küçük bir sensör çıktısı olabilir. Şimdi bir sonraki aşamaya geçiyoruz. Ardından modeli eğiteceğiz. Sonuç olarak genel resmi özetleyeceğiz.",
    "kisa": "Örnek nedir. Neden önemli.",
}


def run():
    for name, text in SCENARIOS.items():
        print(f"===== Senaryo: {name} =====")
        res = compute_pedagogy_metrics(text)
        raw = res['raw']
        scores = res['scores']
        print(f"Sentences: {raw['sentence_count']} | insufficient={raw['insufficient_data']}")
        print("Scores:")
        for k in ['examples','questions','signposting','definitions','summary','balance_bonus','pedagogy_score']:
            print(f"  {k:15s}: {scores.get(k,0):.3f}")
        print()


if __name__ == '__main__':
    run()
