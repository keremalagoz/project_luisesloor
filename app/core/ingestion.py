"""Ingestion modülü
PDF/TXT okuma, normalize etme ve temel meta üretimi.

Fonksiyonlar:
	read_pdf(file_bytes: bytes) -> str
	read_txt(file_bytes: bytes) -> str
	normalize_text(text: str) -> str
	basic_text_stats(text: str) -> dict

Not: Chunking bu modülde değil; ayrı adımda (chunking & index) eklenecek.
"""

from __future__ import annotations

from io import BytesIO
from typing import Dict
import re


def read_pdf(file_bytes: bytes) -> str:
	"""Önce pdfminer.six ile dene; hata durumunda PyPDF2 fallback.
	Dönen değer ham (normalize edilmemiş) metindir.
	"""
	text = ""
	bio = BytesIO(file_bytes)
	# pdfminer
	try:
		from pdfminer.high_level import extract_text  # type: ignore
		text = extract_text(bio) or ""
	except Exception:
		text = ""
	if not text.strip():
		# Fallback PyPDF2
		try:
			import PyPDF2  # type: ignore
			bio.seek(0)
			reader = PyPDF2.PdfReader(bio)
			pages = []
			for page in reader.pages:
				try:
					pages.append(page.extract_text() or "")
				except Exception:
					continue
			text = "\n".join(pages)
		except Exception:
			return ""
	return text or ""


def read_txt(file_bytes: bytes) -> str:
	try:
		return file_bytes.decode("utf-8", errors="ignore")
	except Exception:
		return file_bytes.decode("latin-1", errors="ignore")


_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
	"""Basit temizleme: BOM, fazla boşluk, çoklu newline azaltma."""
	if not text:
		return ""
	t = text.replace("\ufeff", "").strip()
	# Satır sonu normalize
	t = t.replace("\r\n", "\n").replace("\r", "\n")
	# Çok uzun boşlukları daralt
	t = _MULTI_SPACE_RE.sub(" ", t)
	# Birden fazla boş satırı iki satıra indir
	t = _MULTI_NL_RE.sub("\n\n", t)
	return t.strip()


def basic_text_stats(text: str) -> Dict[str, int]:
	words = text.split()
	return {
		"chars": len(text),
		"words": len(words),
		# Yaklaşık token (tiktoken öncesi) kelime * 1.3; gerçek hesap chunking aşamasında tiktoken ile yapılacak
		"approx_tokens": int(len(words) * 1.3),
		"lines": text.count("\n") + 1 if text else 0,
	}

