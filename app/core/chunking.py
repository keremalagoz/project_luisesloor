"""Metni token bazlı chunk'lara bölen yardımcı modül.

Kurallar:
- cl100k_base tokenizer (tiktoken) kullanılır.
- max_tokens (default 450), overlap (default 50)
- Çok kısa ( < min_chunk_tokens default 20 ) parçalar elenir.
- Cümle sınırlarını yumuşatma: Basit cümle split yardımı (nokta, soru, ünlem) sonrasında greedy birleştirme.

Çıktı veri yapısı list[dict]:
{
  'id': 'c1',
  'text': '...',
  'token_count': 123,
  'start_token': 0,
  'end_token': 122
}
"""
from __future__ import annotations

from typing import List, Dict, Iterable
import re

try:
    import tiktoken  # type: ignore
except ImportError:  # güvenli fallback (uygulama çalışsın diye)
    tiktoken = None  # type: ignore

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _get_tokenizer(name: str = "cl100k_base"):
    if tiktoken is None:
        raise RuntimeError("tiktoken yüklü değil. requirements.txt güncel mi?")
    return tiktoken.get_encoding(name)


def approximate_tokens(word_count: int) -> int:
    return int(word_count * 1.3)


def simple_sentence_split(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    # Satır sonlarını boşluk yap ki bölme sapıtmasın
    tmp = re.sub(r"[\r\n]+", " ", text)
    parts = _SENT_SPLIT_RE.split(tmp)
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned


def tokenize(text: str, tokenizer=None) -> List[int]:
    if tokenizer is None:
        tokenizer = _get_tokenizer()
    return tokenizer.encode(text)


def detokenize(tokens: List[int], tokenizer=None) -> str:
    if tokenizer is None:
        tokenizer = _get_tokenizer()
    return tokenizer.decode(tokens)


def chunk_sentences(
    sentences: List[str],
    max_tokens: int = 450,
    overlap: int = 50,
    min_chunk_tokens: int = 20,
    store_tokens: bool = False,
) -> List[Dict]:
    if not sentences:
        return []
    tokenizer = _get_tokenizer()

    chunks: List[Dict] = []
    current_tokens: List[int] = []
    current_texts: List[str] = []
    start_token_index = 0

    def flush():
        nonlocal start_token_index, current_tokens, current_texts
        if not current_tokens:
            return
        if len(current_tokens) < min_chunk_tokens:
            # Çok küçük; atla
            current_tokens = []
            current_texts = []
            return
        chunk_id = f"c{len(chunks)+1}"
        chunk_text = detokenize(current_tokens, tokenizer)
        end_token_index = start_token_index + len(current_tokens) - 1
        chunk_obj = {
            'id': chunk_id,
            'text': chunk_text,
            'token_count': len(current_tokens),
            'start_token': start_token_index,
            'end_token': end_token_index,
        }
        if store_tokens:
            # Derin kopya – değişmesin
            chunk_obj['tokens'] = list(current_tokens)
        chunks.append(chunk_obj)
        # Overlap uygula
        if overlap > 0:
            keep = current_tokens[-overlap:]
            start_token_index = end_token_index + 1 - len(keep)
            current_tokens = keep[:]
            # Metnin son cümlesi heuristik olarak yeterli; yeniden inşa et
            # Orijinal sentence'lar saklamadığımız için basit dekod kullanıyoruz
            current_texts = [detokenize(keep, tokenizer)]
        else:
            current_tokens = []
            current_texts = []
            start_token_index = end_token_index + 1

    for sent in sentences:
        sent_tokens = tokenize(sent, tokenizer)
        if not sent_tokens:
            continue
        # Eğer tek cümle bile limitten büyükse: hard split
        if len(sent_tokens) > max_tokens:
            # Parçalara böl
            for i in range(0, len(sent_tokens), max_tokens):
                piece = sent_tokens[i:i+max_tokens]
                if current_tokens:
                    flush()
                current_tokens = piece
                current_texts = [detokenize(piece, tokenizer)]
                flush()
            continue
        prospective_len = len(current_tokens) + len(sent_tokens)
        if prospective_len <= max_tokens:
            current_tokens.extend(sent_tokens)
            current_texts.append(sent)
        else:
            flush()
            current_tokens = sent_tokens[:]
            current_texts = [sent]
    # Son kalan
    flush()
    return chunks


def tokenize_and_chunk(
    text: str,
    max_tokens: int = 450,
    overlap: int = 50,
    min_chunk_tokens: int = 20,
    store_tokens: bool = False,
) -> List[Dict]:
    sents = simple_sentence_split(text)
    return chunk_sentences(
        sents,
        max_tokens=max_tokens,
        overlap=overlap,
        min_chunk_tokens=min_chunk_tokens,
        store_tokens=store_tokens,
    )

__all__ = [
    'tokenize_and_chunk',
    'chunk_sentences',
    'simple_sentence_split'
]


def validate_overlap(chunks: List[Dict], overlap: int) -> bool:
    """Overlap doğrulama yardımcı fonksiyonu.
    Mantık: Her ardışık çifttte chunk[i] son overlap token'ı == chunk[i+1] ilk overlap token'ı.
    Not: Eğer chunk sayısı < 2 veya overlap == 0 -> True döner.
    """
    if overlap <= 0:
        return True
    if len(chunks) < 2:
        return True
    tok = None
    for a, b in zip(chunks, chunks[1:]):
        if 'tokens' in a and 'tokens' in b:
            ta = a['tokens']
            tb = b['tokens']
        else:
            if tok is None:
                tok = _get_tokenizer()
            ta = tok.encode(a['text'])
            tb = tok.encode(b['text'])
        if len(ta) < overlap or len(tb) < overlap:
            # Chunk çok küçükse katı kontrolü atlıyoruz
            continue
        if ta[-overlap:] != tb[:overlap]:
            return False
    return True

__all__.append('validate_overlap')
