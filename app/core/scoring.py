"""Toplam skor agregasyon modülü.
Coverage + Delivery + Pedagogy birleşik skorunu hesaplar.
"""
from __future__ import annotations
from typing import Dict, Optional

DEFAULT_WEIGHTS = {
	'coverage': 0.5,
	'delivery': 0.3,
	'pedagogy': 0.2,
}


def aggregate_scores(
	coverage: Optional[Dict] = None,
	delivery: Optional[Dict] = None,
	pedagogy: Optional[Dict] = None,
	weights: Optional[Dict[str, float]] = None,
) -> Dict:
	"""Verilen alt skor sözlüklerinden toplam skor hesapla.

	Beklenen girişler:
	- coverage['summary']['coverage_ratio'] veya coverage['summary']['weighted_score'] (fallback coverage_ratio)
	- delivery['scores']['delivery_score']
	- pedagogy['scores']['pedagogy_score']

	Eksik olan modüller skor=0 kabul edilir.
	Ağırlıklar normalizasyonu otomatik (toplamı !=1 ise yeniden ölçeklenir).
	"""
	w = dict(DEFAULT_WEIGHTS)
	if weights:
		w.update(weights)

	total_w = sum(w.values()) or 1.0
	for k in w:
		w[k] = w[k] / total_w

	cov_score = 0.0
	if coverage:
		summ = coverage.get('summary', {})
		cov_score = summ.get('weighted_score') or summ.get('coverage_ratio') or 0.0
	del_score = 0.0
	if delivery:
		del_score = delivery.get('scores', {}).get('delivery_score', 0.0)
	ped_score = 0.0
	if pedagogy:
		ped_score = pedagogy.get('scores', {}).get('pedagogy_score', 0.0)

	combined = cov_score * w['coverage'] + del_score * w['delivery'] + ped_score * w['pedagogy']

	return {
		'inputs': {
			'coverage': cov_score,
			'delivery': del_score,
			'pedagogy': ped_score,
		},
		'weights_used': w,
		'total_score': combined,
	}

__all__ = ['aggregate_scores']
