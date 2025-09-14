"""Run history & karşılaştırma yardımcıları.

Bu modül SQLite storage'dan çekilmiş run detay objelerini (fetch_run_details
çıktısı şekli) kullanarak metrik karşılaştırmaları üretir.

compare_runs(run_a, run_b) çıktısı:
{
  'metrics': [
      { 'category': 'delivery', 'name': 'wpm', 'a': 0.72, 'b': 0.80, 'delta': 0.08, 'direction': 'up' },
      ...
  ],
  'summary': {
      'total_score_a': 0.75,
      'total_score_b': 0.81,
      'total_score_delta': 0.06,
      'count_improved': 5,
      'count_declined': 2,
      'count_unchanged': 3,
      'avg_delta': 0.01
  }
}
"""
from __future__ import annotations

from typing import Dict, Any, List


def _index_metrics(run: Dict[str, Any]) -> Dict[tuple, Dict[str, Any]]:
    idx = {}
    for m in run.get('metrics', []) or []:
        # Yalnızca skor alanı numeric olanları karşılaştırmada dikkate al
        score = m.get('score')
        if isinstance(score, (int, float)):
            idx[(m.get('category'), m.get('name'))] = m
    return idx


def compare_runs(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> Dict[str, Any]:
    """İki run detay objesini skor bazında karşılaştır.

    Sadece her iki tarafta da bulunan (category,name) çiftleri ve numerik skorlar
    karşılaştırılır. Delta = b - a. direction: up|down|flat
    """
    idx_a = _index_metrics(run_a)
    idx_b = _index_metrics(run_b)
    common_keys = sorted(set(idx_a.keys()) & set(idx_b.keys()))

    rows: List[Dict[str, Any]] = []
    improved = declined = unchanged = 0
    deltas = []
    for key in common_keys:
        ma = idx_a[key]
        mb = idx_b[key]
        a_score = ma.get('score')
        b_score = mb.get('score')
        if not isinstance(a_score, (int, float)) or not isinstance(b_score, (int, float)):
            continue
        delta = b_score - a_score
        if delta > 1e-9:
            direction = 'up'
            improved += 1
        elif delta < -1e-9:
            direction = 'down'
            declined += 1
        else:
            direction = 'flat'
            unchanged += 1
        deltas.append(delta)
        rows.append({
            'category': key[0],
            'name': key[1],
            'a': a_score,
            'b': b_score,
            'delta': delta,
            'direction': direction,
        })

    total_a = run_a.get('total_score')
    total_b = run_b.get('total_score')
    total_delta = None
    if isinstance(total_a, (int, float)) and isinstance(total_b, (int, float)):
        total_delta = total_b - total_a

    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
    summary = {
        'total_score_a': total_a,
        'total_score_b': total_b,
        'total_score_delta': total_delta,
        'count_improved': improved,
        'count_declined': declined,
        'count_unchanged': unchanged,
        'avg_delta': avg_delta,
        'metric_count': len(rows),
    }
    return {
        'metrics': rows,
        'summary': summary,
    }


__all__ = ['compare_runs']
