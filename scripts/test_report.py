"""Rapor modülü test scripti.
Çalıştırma: python scripts/test_report.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.core.report import build_report_data, render_markdown, export_json  # noqa

MOCK_SOURCE = {
    'filename': 'demo.txt',
    'stats': {
        'words': 250,
        'chars': 1400,
        'approx_tokens': 300
    }
}

MOCK_COVERAGE = {
    'summary': {
        'covered': 5,
        'partial': 2,
        'missing': 1,
        'coverage_ratio': 0.70,
    },
    'topics': [
        {'topic': 'Giriş', 'status': 'covered', 'max_similarity': 0.81},
        {'topic': 'Tanımlar', 'status': 'partial', 'max_similarity': 0.68},
        {'topic': 'Örnekler', 'status': 'covered', 'max_similarity': 0.83},
    ]
}

MOCK_DELIVERY = {
    'raw': {
        'wpm': 145,
        'filler_ratio': 0.03,
        'avg_sentence_len': 14.2,
        'pause_density': 0.05,
    },
    'scores': {
        'wpm': 0.95,
        'filler': 0.90,
        'repetition': 0.85,
        'sentence_length': 0.92,
        'pause': 0.88,
        'delivery_score': 0.90,
    }
}

MOCK_PEDAGOGY = {
    'raw': {
        'sentence_count': 32,
        'counts': {'examples': 5, 'questions': 3, 'signposting': 7, 'definitions': 2, 'summary': 1},
        'ratios': {'examples': 0.156, 'questions': 0.094, 'signposting': 0.219, 'definitions': 0.063, 'summary': 0.031},
        'insufficient_data': False,
    },
    'scores': {
        'examples': 1.0,
        'questions': 0.94,
        'signposting': 0.80,
        'definitions': 0.79,
        'summary': 0.78,
        'balance_bonus': 0.05,
        'pedagogy_score': 0.90,
    }
}

MOCK_SCORING = {
    'inputs': {'coverage': 0.70, 'delivery': 0.90, 'pedagogy': 0.90},
    'weights_used': {'coverage': 0.5, 'delivery': 0.3, 'pedagogy': 0.2},
    'total_score': 0.80,
}


def run():
    data = build_report_data(
        source_meta=MOCK_SOURCE,
        coverage=MOCK_COVERAGE,
        delivery=MOCK_DELIVERY,
        pedagogy=MOCK_PEDAGOGY,
        scoring=MOCK_SCORING,
    )
    md = render_markdown(data)
    js = export_json(data)
    print("=== JSON Özet (ilk 300 char) ===")
    print(js[:300] + ('...' if len(js) > 300 else ''))
    print("\n=== Markdown İlk 40 Satır ===")
    lines = md.splitlines()
    for line in lines[:40]:
        print(line)
    print("\nTam Markdown uzunluğu:", len(md.splitlines()), "satır")


if __name__ == '__main__':
    run()
