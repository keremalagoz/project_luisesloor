"""Basit kural tabanlı öneri motoru.

Girdi sözleşmesi (opsiyonel parametreler boş olabilir):
 - coverage: {'summary': {'coverage_ratio': float, ...}, 'topics': [{'topic': str, 'status': str, 'max_similarity': float}]}
 - delivery: {'scores': {...}, 'raw': {...}}
 - pedagogy: {'scores': {...}, 'raw': {'counts': {...}, 'ratios': {...}}}
 - scoring: aggregate_scores çıktısı

Çıktı formatı:
{
  'recommendations': [
       {
          'category': 'coverage' | 'delivery' | 'pedagogy' | 'overall',
          'severity': 'high' | 'medium' | 'low',
          'message': '...',
          'rationale': 'kısa açıklama',
          'meta': {...} (opsiyonel ek veri)
       }, ...
  ],
  'summary': {
       'counts': {'high': n, 'medium': n, 'low': n},
       'total': int
  }
}

Not: Heuristikler basit; ileride ML tabanlı öneriler / LLM chain ile genişletilebilir.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional


def _add(rec_list: List[Dict[str, Any]], category: str, severity: str, message: str, rationale: str, meta: Optional[Dict[str, Any]] = None):
    rec_list.append({
        'category': category,
        'severity': severity,
        'message': message,
        'rationale': rationale,
        'meta': meta or {}
    })


def _severity(score: float, invert: bool = False) -> str:
    """Skor yüksekse iyi varsayar; invert=True ise düşük skorlar iyi demektir.
    Eşikler: >=0.75 iyi(low), 0.5-0.75 orta(medium), <0.5 zayıf(high)
    """
    if invert:
        # invert: yüksek skor kötü (ör: filler_ratio)
        if score >= 0.75:
            return 'high'
        if score >= 0.5:
            return 'medium'
        return 'low'
    # normal
    if score >= 0.75:
        return 'low'
    if score >= 0.5:
        return 'medium'
    return 'high'


def generate_recommendations(
    coverage: Optional[Dict[str, Any]] = None,
    delivery: Optional[Dict[str, Any]] = None,
    pedagogy: Optional[Dict[str, Any]] = None,
    scoring: Optional[Dict[str, Any]] = None,
    max_recs: int = 25,
) -> Dict[str, Any]:
    recs: List[Dict[str, Any]] = []

    # Coverage heuristikleri
    if coverage:
        summ = coverage.get('summary') or {}
        cov_ratio = summ.get('coverage_ratio')
        if isinstance(cov_ratio, (int, float)):
            sev = _severity(cov_ratio)
            if sev in ('medium','high'):
                _add(
                    recs,
                    'coverage',
                    sev,
                    'Coverage oranını artırmak için eksik veya partial konuları güçlendir.',
                    f'coverage_ratio={cov_ratio:.2f}',
                    {'coverage_ratio': cov_ratio}
                )
        topics = coverage.get('topics') or []
        missing = [t for t in topics if t.get('status') == 'missing']
        partial = [t for t in topics if t.get('status') == 'partial']
        if missing:
            _add(
                recs,
                'coverage',
                'high',
                f'{len(missing)} konu eksik: İçeriğe ilgili örnek, tanım veya açıklama ekleyin.',
                'Eksik konular listesi meta içinde.',
                {'missing_topics': [m.get('topic') for m in missing[:10]]}
            )
        if partial:
            _add(
                recs,
                'coverage',
                'medium',
                f'{len(partial)} konu kısmen kapsanmış: Derinlik ve örnek sayısını artırın.',
                'Partial konular hedef benzerliği eşiğini geçmemiş.',
                {'partial_topics': [p.get('topic') for p in partial[:10]]}
            )

    # Delivery heuristikleri
    if delivery:
        scores = delivery.get('scores') or {}
        raw = delivery.get('raw') or {}
        # WPM - ideal aralık heuristiği (çok yavaş veya çok hızlı)
        wpm_score = scores.get('wpm')
        if isinstance(wpm_score, (int, float)):
            sev = _severity(wpm_score)
            if sev in ('medium','high'):
                _add(
                    recs, 'delivery', sev,
                    'Konuşma hızını optimize et (ne çok hızlı ne çok yavaş).',
                    f'wpm_score={wpm_score:.2f}'
                )
        filler_score = scores.get('filler')
        if isinstance(filler_score, (int, float)):
            sev = _severity(1 - filler_score)  # filler skoru yüksekse iyi, düşükse kötü varsayıyoruz
            if sev in ('medium','high'):
                _add(
                    recs, 'delivery', sev,
                    'Filler kullanımını azalt ("eee", "aslında", "şey" vb.).',
                    f'filler_score={filler_score:.2f}'
                )
        repetition_score = scores.get('repetition')
        if isinstance(repetition_score, (int, float)):
            sev = _severity(repetition_score)
            if sev in ('medium','high'):
                _add(
                    recs, 'delivery', sev,
                    'Tekrar oranını düşür: farklı ifadelerle çeşitlendir.',
                    f'repetition_score={repetition_score:.2f}'
                )
        sentence_len_score = scores.get('sentence_length')
        if isinstance(sentence_len_score, (int, float)):
            sev = _severity(sentence_len_score)
            if sev in ('medium','high'):
                _add(
                    recs, 'delivery', sev,
                    'Cümle uzunluğu dengesini iyileştir (çok uzun/karmaşık cümleleri sadeleştir).',
                    f'sentence_length_score={sentence_len_score:.2f}'
                )
        pause_score = scores.get('pause')
        if isinstance(pause_score, (int, float)):
            sev = _severity(pause_score)
            if sev in ('medium','high'):
                _add(
                    recs, 'delivery', sev,
                    'Uygun duraklamaları optimize et; kritik noktalarda kısa duraklar ekle.',
                    f'pause_score={pause_score:.2f}'
                )
        if raw.get('insufficient_data'):
            _add(
                recs, 'delivery', 'high',
                'Veri yetersiz (kelime sayısı düşük). Daha uzun bir örnek kaydet.',
                'Minimum kelime eşiği altı.'
            )

    # Pedagogy heuristikleri
    if pedagogy:
        p_scores = pedagogy.get('scores') or {}
        p_raw = pedagogy.get('raw') or {}
        for key in ['examples','questions','signposting','definitions','summary']:
            val = p_scores.get(key)
            if isinstance(val, (int,float)):
                sev = _severity(val)
                if sev in ('medium','high'):
                    msg_map = {
                        'examples': 'Daha fazla somut örnek ekleyerek kavramları pekiştir.',
                        'questions': 'İzleyiciyi dahil etmek için sorular sor.',
                        'signposting': 'Bölümler arası geçişleri netleştir ("Şimdi ... hakkında konuşacağız").',
                        'definitions': 'Temel terimler için kısa ve net tanımlar ekle.',
                        'summary': 'Bölüm sonlarında özet cümleleri kullan.',
                    }
                    _add(
                        recs, 'pedagogy', sev,
                        msg_map.get(key, key),
                        f'{key}_score={val:.2f}'
                    )
        if p_raw.get('insufficient_data'):
            _add(
                recs, 'pedagogy', 'high',
                'Pedagojik sinyaller az (cümle sayısı yetersiz). Daha uzun bir içerik üret.',
                'Min cümle eşiği altı.'
            )

    # Genel / overall
    if scoring:
        total = scoring.get('total_score')
        if isinstance(total, (int,float)):
            sev = _severity(total)
            if sev == 'high':
                _add(
                    recs, 'overall', 'high',
                    'Genel skor düşük: Öncelik sırası: Coverage > Delivery > Pedagogy eksiklerini sırayla iyileştir.',
                    f'total_score={total:.2f}'
                )
            elif sev == 'medium':
                _add(
                    recs, 'overall', 'medium',
                    'Genel skor orta: Birkaç odaklı iyileştirme ile 0.75+ bandına çıkabilir.',
                    f'total_score={total:.2f}'
                )

    # Sıralama: severity (high > medium > low), ardından kategori
    severity_rank = {'high': 0, 'medium': 1, 'low': 2}
    recs.sort(key=lambda r: (severity_rank.get(r['severity'], 9), r['category']))

    if len(recs) > max_recs:
        recs = recs[:max_recs]

    counts = {'high':0,'medium':0,'low':0}
    for r in recs:
        counts[r['severity']] = counts.get(r['severity'],0)+1

    return {
        'recommendations': recs,
        'summary': {
            'counts': counts,
            'total': len(recs),
        }
    }


__all__ = ['generate_recommendations']
