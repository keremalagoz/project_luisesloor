"""Embeddings modülü
Gemini embedding çağrıları + disk cache + cosine similarity yardımcıları.

Cache Stratejisi:
- Dosya: `.cache/embeddings.jsonl` (her satır: {"key":sha256, "model":..., "text_sha":..., "vector":[...]})
- Anahtar: sha256(model_name + "::" + chunk_text)
- Bellek: process süresince dict cache

Not: Şu an gerçek Gemini çağrısı TODO bırakıldı; entegrasyon için
google-generativeai import edilip API anahtarı secrets'tan alınacak.
Hackathon hız avantajı için önce yapı kurulur, sonra gerçek çağrı eklenir.
"""
from __future__ import annotations

import os, json, hashlib
from typing import List, Dict, Optional

_EMBED_CACHE_PATH = os.path.join('.cache', 'embeddings.jsonl')
_memory_cache: Dict[str, List[float]] = {}


def _ensure_cache_dir():
	os.makedirs(os.path.dirname(_EMBED_CACHE_PATH), exist_ok=True)


def _hash_key(model: str, text: str) -> str:
	h = hashlib.sha256()
	h.update((model + '::' + text).encode('utf-8'))
	return h.hexdigest()


def _hash_text(text: str) -> str:
	return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_disk_cache() -> None:
	if not os.path.exists(_EMBED_CACHE_PATH):
		return
	try:
		with open(_EMBED_CACHE_PATH, 'r', encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				if not line:
					continue
				try:
					obj = json.loads(line)
					_memory_cache[obj['key']] = obj['vector']
				except Exception:
					continue
	except Exception:
		pass


def append_disk_cache(entries: List[Dict]):
	if not entries:
		return
	_ensure_cache_dir()
	with open(_EMBED_CACHE_PATH, 'a', encoding='utf-8') as f:
		for e in entries:
			f.write(json.dumps(e, ensure_ascii=False) + '\n')


def cosine_similarity(a: List[float], b: List[float]) -> float:
	import math
	if len(a) != len(b) or not a:
		return 0.0
	dot = sum(x*y for x, y in zip(a, b))
	na = math.sqrt(sum(x*x for x in a))
	nb = math.sqrt(sum(x*x for x in b))
	if na == 0 or nb == 0:
		return 0.0
	return dot / (na * nb)


def _fake_embed(text: str, dim: int = 8) -> List[float]:
	"""Geçici düşük boyut deterministic vektör (placeholder)."""
	# Deterministic pseudo-random: hash -> ints -> normalize
	h = hashlib.sha256(text.encode('utf-8')).digest()
	arr = [int.from_bytes(h[i:i+4], 'little', signed=False) / 2**32 for i in range(0, dim*4, 4)]
	# Normalize
	import math
	norm = math.sqrt(sum(x*x for x in arr)) or 1.0
	return [x / norm for x in arr]


def embed_texts(texts: List[str], model: str = 'text-embedding-004', use_real: bool = False) -> List[List[float]]:
	"""Gerçek Gemini entegrasyonu TODO: use_real=True olduğunda google-generativeai çağır.
	Şimdilik hızlı prototip için _fake_embed.
	"""
	vectors: List[List[float]] = []
	if use_real:
		# TODO: gerçek API entegrasyonu
		# import google.generativeai as genai
		# genai.configure(api_key=...)
		# ... çağrı ve sonuç parse ...
		pass
	for t in texts:
		vectors.append(_fake_embed(t))
	return vectors


def get_or_compute_embeddings(chunks: List[Dict], model: str = 'text-embedding-004', use_real: bool = False) -> List[Dict]:
	load_disk_cache()  # idempotent
	new_entries = []
	output = []
	to_compute: List[str] = []
	missing_indices: List[int] = []
	for idx, ch in enumerate(chunks):
		key = _hash_key(model, ch['text'])
		if key in _memory_cache:
			output.append({**ch, 'embedding': _memory_cache[key]})
		else:
			to_compute.append(ch['text'])
			missing_indices.append(idx)
			output.append(None)  # placeholder
	if to_compute:
		vectors = embed_texts(to_compute, model=model, use_real=use_real)
		for local_i, vec in enumerate(vectors):
			global_idx = missing_indices[local_i]
			ch = chunks[global_idx]
			key = _hash_key(model, ch['text'])
			_memory_cache[key] = vec
			entry = {
				'key': key,
				'model': model,
				'text_sha': _hash_text(ch['text']),
				'vector': vec,
			}
			new_entries.append(entry)
			output[global_idx] = {**ch, 'embedding': vec}
		append_disk_cache(new_entries)
	# Filtre: placeholder kalmamalı
	return [o for o in output if o is not None]


__all__ = [
	'embed_texts',
	'get_or_compute_embeddings',
	'cosine_similarity'
]
