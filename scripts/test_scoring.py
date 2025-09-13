"""Scoring agregasyon test scripti.
Çalıştırma: python scripts/test_scoring.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.scoring import aggregate_scores  # noqa

MOCK_COVERAGE = {
    'summary': {
        'covered': 8,
        'partial': 2,
        'missing': 0,
        'coverage_ratio': 0.85,
        'weighted_score': 0.88,
    }
}

MOCK_DELIVERY = {
    'scores': {
        'delivery_score': 0.74
    }
}

MOCK_PEDAGOGY = {
    'scores': {
        'pedagogy_score': 0.62
    }
}


def run():
    print("=== Varsayılan Ağırlıklarla ===")
    res_default = aggregate_scores(MOCK_COVERAGE, MOCK_DELIVERY, MOCK_PEDAGOGY)
    print(res_default)
    print()

    print("=== Özel Ağırlıklarla (coverage=0.4, delivery=0.4, pedagogy=0.2) ===")
    res_custom = aggregate_scores(MOCK_COVERAGE, MOCK_DELIVERY, MOCK_PEDAGOGY, weights={'coverage':0.4,'delivery':0.4,'pedagogy':0.2})
    print(res_custom)
    print()

    print("=== Eksik Modüller (yalnızca coverage) ===")
    res_partial = aggregate_scores(MOCK_COVERAGE, None, None)
    print(res_partial)
    print()

    print("=== Coverage weighted_score yok fallback coverage_ratio ===")
    cov2 = {'summary': {'coverage_ratio': 0.6}}
    res_fb = aggregate_scores(cov2, MOCK_DELIVERY, MOCK_PEDAGOGY)
    print(res_fb)


if __name__ == '__main__':
    run()
