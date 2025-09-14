"""Trend / progress hesaplama yardımcıları.

Bu modül run geçmişi üzerinden skor serileri ve delta özetleri çıkarır.
"""
from __future__ import annotations

from typing import List, Dict, Any
import math

def prepare_run_dataframe(runs: List[Dict[str, Any]]):  # type: ignore[override]
    """Run list (dict) -> pandas DataFrame (sorted by created_at if exists else id)."""
    import pandas as pd
    if not runs:
        return pd.DataFrame(columns=[
            'id','created_at','total_score','coverage_score','delivery_score','pedagogy_score'
        ])
    df = pd.DataFrame(runs)
    # Sütun normalizasyonu: bazı alan isimleri farklı olabilir; güvenli rename denemesi.
    rename_map = {}
    # created_at yoksa id bazlı sort
    if 'created_at' in df.columns:
        df = df.sort_values('created_at')
    else:
        df = df.sort_values('id')
    # Index reset
    df = df.reset_index(drop=True)
    return df


def compute_basic_deltas(df):
    """İlk ve son run arasındaki delta sözlüğü.
    Yoksa boş dict.
    """
    if df is None or df.empty or len(df) < 2:
        return {}
    first = df.iloc[0]
    last = df.iloc[-1]
    def delta(col):
        a = first.get(col)
        b = last.get(col)
        if a is None or b is None or not isinstance(a, (int,float)) or not isinstance(b,(int,float)):
            return None
        return b - a
    out = {
        'total_score_delta': delta('total_score'),
        'coverage_score_delta': delta('coverage_score'),
        'delivery_score_delta': delta('delivery_score'),
        'pedagogy_score_delta': delta('pedagogy_score'),
    }
    return out


def top_improvements(df, metric_cols, top_n=3):
    """Her metrik için (son - ilk) delta hesaplayıp pozitifleri büyükten küçüğe sıralar.
    Negative olanlar decline hesabına gidecek.
    Dönüş: { 'improved': [(metric, delta), ...], 'declined': [...]}"""
    if df is None or df.empty or len(df) < 2:
        return {'improved': [], 'declined': []}
    first = df.iloc[0]
    last = df.iloc[-1]
    deltas = []
    for m in metric_cols:
        a = first.get(m)
        b = last.get(m)
        if isinstance(a,(int,float)) and isinstance(b,(int,float)):
            deltas.append((m, b - a))
    improved = sorted([d for d in deltas if d[1] > 0], key=lambda x: x[1], reverse=True)[:top_n]
    declined = sorted([d for d in deltas if d[1] < 0], key=lambda x: x[1])[:top_n]
    return {'improved': improved, 'declined': declined}


def annotate_threshold_color(value: float) -> str:
    if value is None or not isinstance(value,(int,float)) or math.isnan(value):
        return 'gray'
    if value >= 0.8:
        return 'green'
    if value >= 0.6:
        return 'orange'
    return 'red'


__all__ = [
    'prepare_run_dataframe',
    'compute_basic_deltas',
    'top_improvements',
    'annotate_threshold_color'
]
