"""Pedagogy metrikleri hesaplama modülü.
Heuristik dayalı oran çıkarımı ve normalizasyon.
"""
from __future__ import annotations
from typing import Dict, List, Optional
import re
import math

DEFAULT_CONFIG = {
	'targets': {
		'examples': 0.15,
		'questions': 0.10,
		'signposting': 0.18,
		'definitions': 0.08,
		'summary': 0.04,
	},
	'weights': {
		'examples': 0.25,
		'questions': 0.20,
		'signposting': 0.20,
		'definitions': 0.15,
		'summary': 0.15,
		'balance_bonus': 0.05,  # bonus eklenecek, skor cap 1.0
	},
	'min_sentences': 10,
}

# Heuristik pattern listeleri
EXAMPLE_PATTERNS = [r"\börnek\b", r"\bmesela\b", r"örneğin", r"ör\.?"]
QUESTION_PATTERNS = [r"neden", r"nasıl", r"hangi", r"kim", r"ne zaman", r"düşünün", r"sizce", r"sence"]
SIGNPOST_PATTERNS = [
	r"önce", r"sonra", r"şimdi", r"ilk olarak", r"ardından", r"özetle", r"sonuç olarak",
	r"bir sonraki", r"temel olarak", r"daha sonra", r"takip eden"
]
DEFINITION_PATTERNS = [r"tanımı", r"nedir", r"olarak tanımlanır", r"ifade edilir", r"diyebiliriz", r"denir"]
SUMMARY_PATTERNS = [r"özetle", r"kısaca", r"toparlarsak", r"sonuç olarak", r"tekrar edelim", r"genel olarak"]

SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> List[str]:
	t = text.strip()
	if not t:
		return []
	t = re.sub(r"[\r\n]+", " ", t)
	parts = SENT_SPLIT_RE.split(t)
	return [p.strip() for p in parts if p.strip()]


def _norm_score(ratio: float, target: float) -> float:
	if target <= 0:
		return 0.0
	if ratio <= 0:
		return 0.0
	if ratio <= target:
		return min(1.0, ratio / target)
	if ratio <= 2 * target:
		return 1.0
	excess = ratio - 2 * target
	penalty = min(0.4, excess / (2 * target))
	return max(0.0, 1.0 - penalty)


def _count_matches(sent: str, patterns: List[str]) -> bool:
	low = sent.lower()
	for pat in patterns:
		if re.search(pat, low):
			return True
	return False


def compute_pedagogy_metrics(
	transcript: str,
	config: Optional[Dict] = None,
) -> Dict:
	cfg = DEFAULT_CONFIG.copy()
	if config:
		for k, v in config.items():
			if isinstance(v, dict) and k in cfg:
				cfg[k].update(v)  # type: ignore
			else:
				cfg[k] = v

	targets = cfg['targets']
	weights = cfg['weights']

	sents = _sentences(transcript)
	sent_count = len(sents)
	insufficient = sent_count < cfg['min_sentences']

	counters = {k: 0 for k in targets.keys()}

	if not insufficient:
		for s in sents:
			if _count_matches(s, EXAMPLE_PATTERNS):
				counters['examples'] += 1
			if _count_matches(s, QUESTION_PATTERNS) or s.strip().endswith('?'):
				counters['questions'] += 1
			if _count_matches(s, SIGNPOST_PATTERNS):
				counters['signposting'] += 1
			if _count_matches(s, DEFINITION_PATTERNS):
				counters['definitions'] += 1
			if _count_matches(s, SUMMARY_PATTERNS):
				counters['summary'] += 1

	ratios = {k: (counters[k] / sent_count if sent_count else 0.0) for k in counters}

	scores = {k: 0.0 for k in counters}
	if not insufficient:
		for k in counters:
			scores[k] = _norm_score(ratios[k], targets[k])
		metric_values = list(scores.values())
		balance_bonus = 0.0
		if metric_values:
			mean = sum(metric_values) / len(metric_values)
			var = sum((v - mean) ** 2 for v in metric_values) / len(metric_values)
			std = math.sqrt(var)
			if std < 0.25:
				balance_bonus = weights.get('balance_bonus', 0.0)
		scores['balance_bonus'] = balance_bonus
	else:
		scores['balance_bonus'] = 0.0

	pedagogy_score = 0.0
	if not insufficient:
		base_sum = sum(scores[k] * weights[k] for k in targets.keys())
		bonus = scores.get('balance_bonus', 0.0)
		pedagogy_score = min(1.0, base_sum + bonus)
	scores['pedagogy_score'] = pedagogy_score

	return {
		'raw': {
			'sentence_count': sent_count,
			'counts': counters,
			'ratios': ratios,
			'insufficient_data': insufficient,
		},
		'scores': scores,
		'weights': weights,
		'config_used': cfg,
	}

__all__ = ['compute_pedagogy_metrics']
