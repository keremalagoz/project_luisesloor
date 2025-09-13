"""Delivery metrikleri hesaplama modülü.

Metrikler:
- WPM (words per minute)
- Filler ratio
- Lexical diversity (type/token) -> repetition skoru
- Average sentence length
- Pause density (heuristic: '...' , boş satır, uzun çizgi vs.)

Çıktı: compute_delivery_metrics(transcript:str, duration_minutes:Optional[float]) -> dict
"""
from __future__ import annotations
from typing import List, Dict, Optional
import re

WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

DEFAULT_CONFIG = {
	'ideal_wpm_min': 130,
	'ideal_wpm_max': 170,
	'filler_tolerance': 0.05,
	'diversity_target': 0.55,
	'sentence_len_min': 8,
	'sentence_len_max': 24,
	'pause_tolerance': 0.10,
	'weights': {
		'wpm': 0.25,
		'filler': 0.25,
		'repetition': 0.25,
		'sentence_length': 0.15,
		'pause': 0.10,
	}
}

DEFAULT_FILLERS = [
	'şey', 'yani', 'hani', 'aslında', 'işte', 'falan', 'gibi', 'efendim', 'ya', 'aynen'
]


def _safe_div(a: float, b: float) -> float:
	return a / b if b else 0.0


def _words(text: str) -> List[str]:
	return [w.lower() for w in WORD_RE.findall(text)]


def _sentences(text: str) -> List[str]:
	t = text.strip()
	if not t:
		return []
	t = re.sub(r"[\r\n]+", " ", t)
	parts = SENT_SPLIT_RE.split(t)
	return [p.strip() for p in parts if p.strip()]


def _count_fillers(words: List[str], fillers: List[str]) -> int:
	fset = set(fillers)
	return sum(1 for w in words if w in fset)


def _lexical_diversity(words: List[str]) -> float:
	if not words:
		return 0.0
	return len(set(words)) / len(words)


def _pause_markers(text: str) -> int:
	return len(re.findall(r"(\.\.\.|…|--)", text)) + text.count('\n\n')


def _normalize_wpm(wpm: float, min_w: float, max_w: float) -> float:
	if wpm <= 0:
		return 0.0
	if wpm < min_w:
		return max(0.0, min(1.0, wpm / min_w * 0.7))
	if wpm > max_w:
		span = max_w
		over = wpm - max_w
		return max(0.0, 1 - (over / span))
	return 1.0


def _normalize_filler(ratio: float, tol: float) -> float:
	if ratio <= 0:
		return 1.0
	if ratio >= 2*tol:
		return 0.0
	if ratio <= tol:
		return 1 - 0.5*(ratio / tol)
	return max(0.0, 0.5 * (1 - (ratio - tol) / tol))


def _normalize_diversity(div: float, target: float) -> float:
	if div <= 0:
		return 0.0
	if div >= target:
		return 1.0
	return div / target


def _normalize_sentence_len(avg_len: float, min_len: float, max_len: float) -> float:
	if avg_len <= 0:
		return 0.0
	if avg_len < min_len:
		return avg_len / min_len * 0.7
	if avg_len > max_len:
		span = max_len
		over = avg_len - max_len
		return max(0.0, 1 - over / span)
	return 1.0


def _normalize_pause(density: float, tol: float) -> float:
	if density <= 0:
		return 1.0
	if density >= 2*tol:
		return 0.0
	if density <= tol:
		return 1 - 0.5*(density / tol)
	return max(0.0, 0.5 * (1 - (density - tol) / tol))


def compute_delivery_metrics(
	transcript: str,
	duration_minutes: Optional[float] = None,
	config: Optional[Dict] = None,
	fillers: Optional[List[str]] = None,
) -> Dict:
	cfg = DEFAULT_CONFIG.copy()
	if config:
		for k, v in config.items():
			if isinstance(v, dict) and k in cfg:
				cfg[k].update(v)  # type: ignore
			else:
				cfg[k] = v
	fillers_list = fillers or DEFAULT_FILLERS

	words = _words(transcript)
	sentences = _sentences(transcript)
	word_count = len(words)
	if not duration_minutes or duration_minutes <= 0:
		duration_minutes = _safe_div(word_count, 150.0)

	unique_words = len(set(words))
	wpm = _safe_div(word_count, duration_minutes)
	filler_count = _count_fillers(words, fillers_list)
	filler_ratio = _safe_div(filler_count, word_count)
	diversity = _lexical_diversity(words)
	sentence_count = len(sentences)
	avg_sentence_len = _safe_div(word_count, sentence_count) if sentence_count else 0.0
	pause_count = _pause_markers(transcript)
	pause_density = _safe_div(pause_count, sentence_count) if sentence_count else 0.0

	insufficient = word_count < 20

	scores = {k: 0.0 for k in ['wpm','filler','repetition','sentence_length','pause']}
	if not insufficient:
		scores['wpm'] = _normalize_wpm(wpm, cfg['ideal_wpm_min'], cfg['ideal_wpm_max'])
		scores['filler'] = _normalize_filler(filler_ratio, cfg['filler_tolerance'])
		scores['repetition'] = _normalize_diversity(diversity, cfg['diversity_target'])
		scores['sentence_length'] = _normalize_sentence_len(avg_sentence_len, cfg['sentence_len_min'], cfg['sentence_len_max'])
		scores['pause'] = _normalize_pause(pause_density, cfg['pause_tolerance'])

	weights = cfg['weights']
	delivery_score = 0.0
	if not insufficient:
		delivery_score = sum(scores[k] * weights[k] for k in scores)
	scores['delivery_score'] = delivery_score

	return {
		'raw': {
			'words': word_count,
			'unique_words': unique_words,
			'duration_minutes': duration_minutes,
			'wpm': wpm,
			'filler_count': filler_count,
			'filler_ratio': filler_ratio,
			'sentence_count': sentence_count,
			'avg_sentence_len': avg_sentence_len,
			'pause_markers': pause_count,
			'pause_density': pause_density,
			'insufficient_data': insufficient,
		},
		'scores': scores,
		'weights': weights,
		'config_used': {k: v for k, v in cfg.items() if k != 'weights'}
	}

__all__ = ['compute_delivery_metrics']
