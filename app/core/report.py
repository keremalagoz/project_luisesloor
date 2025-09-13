"""Rapor üretim modülü.

Amaç: Coverage, Delivery, Pedagogy ve toplam skor çıktılarından
JSON veri yapısı ve Markdown çıktısı üretmek.

PDF dönüşümü bu aşamada eklenmedi (ileride weasyprint / reportlab entegrasyonu için hook bırakıldı).
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


def _safe(d: Optional[dict]) -> dict:
    return d or {}


def build_report_data(
    source_meta: Optional[Dict[str, Any]] = None,
    coverage: Optional[Dict[str, Any]] = None,
    delivery: Optional[Dict[str, Any]] = None,
    pedagogy: Optional[Dict[str, Any]] = None,
    scoring: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ham modül çıktılarından tekleştirilmiş rapor dict'i üretir."""
    now_iso = datetime.utcnow().isoformat() + 'Z'
    data = {
        'generated_at': now_iso,
        'source': source_meta or {},
        'modules': {
            'coverage': coverage or {},
            'delivery': delivery or {},
            'pedagogy': pedagogy or {},
        },
        'scoring': scoring or {},
        'version': '0.1',
    }
    if extra:
        data['extra'] = extra
    return data


def _fmt_score(v: Any) -> str:
    if isinstance(v, (int, float)):
        return f"{v:.2f}"
    return str(v)


def _table(headers: List[str], rows: List[List[str]]) -> str:
    # Basit pipe table
    line_h = '| ' + ' | '.join(headers) + ' |'
    line_s = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
    body = '\n'.join('| ' + ' | '.join(r) + ' |' for r in rows)
    return f"{line_h}\n{line_s}\n{body}"


def render_markdown(report: Dict[str, Any]) -> str:
    src = report.get('source', {})
    modules = report.get('modules', {})
    coverage = modules.get('coverage') or {}
    delivery = modules.get('delivery') or {}
    pedagogy = modules.get('pedagogy') or {}
    scoring = report.get('scoring') or {}

    lines: List[str] = []
    lines.append(f"# Analiz Raporu")
    lines.append("")
    lines.append(f"Oluşturulma: {report.get('generated_at','')}  ")
    if src:
        lines.append("## Kaynak")
        lines.append(f"**Dosya:** {src.get('filename','-')}  ")
        stats = src.get('stats') or {}
        lines.append(f"**Kelime:** {stats.get('words','-')} | **Karakter:** {stats.get('chars','-')} | **Approx Tokens:** {stats.get('approx_tokens','-')}")
        lines.append("")

    # Skor Özeti
    cov_ratio = (coverage.get('summary') or {}).get('coverage_ratio')
    del_score = (delivery.get('scores') or {}).get('delivery_score')
    ped_score = (pedagogy.get('scores') or {}).get('pedagogy_score')
    total_score = scoring.get('total_score')
    lines.append("## Skor Özeti")
    headers = ["Metri̇k","Skor"]
    rows = [
        ["Coverage", _fmt_score(cov_ratio) if cov_ratio is not None else 'N/A'],
        ["Delivery", _fmt_score(del_score) if del_score is not None else 'N/A'],
        ["Pedagogy", _fmt_score(ped_score) if ped_score is not None else 'N/A'],
        ["Toplam", _fmt_score(total_score) if total_score is not None else 'N/A'],
    ]
    lines.append(_table(headers, rows))
    lines.append("")

    # Coverage Detay
    if coverage:
        lines.append("## Coverage Detay")
        summ = coverage.get('summary') or {}
        lines.append(f"Covered: {summ.get('covered','-')} | Partial: {summ.get('partial','-')} | Missing: {summ.get('missing','-')} | Ratio: {_fmt_score(summ.get('coverage_ratio','-'))}")
        topics = coverage.get('topics') or []
        if topics:
            trows = []
            for t in topics:
                trows.append([
                    str(t.get('topic','')),
                    t.get('status',''),
                    _fmt_score(t.get('max_similarity',0.0)),
                ])
            lines.append(_table(["Topic","Status","MaxSim"], trows))
        lines.append("")

    # Delivery Detay
    if delivery:
        lines.append("## Delivery Detay")
        raw = delivery.get('raw') or {}
        scores = delivery.get('scores') or {}
        drows = []
        for k in ['wpm','filler_ratio','avg_sentence_len','pause_density']:
            if k in raw:
                drows.append([k, _fmt_score(raw[k])])
        lines.append(_table(["Ham Metrik","Değer"], drows))
        srows = []
        for k in ['wpm','filler','repetition','sentence_length','pause','delivery_score']:
            if k in scores:
                srows.append([k, _fmt_score(scores[k])])
        lines.append("")
        lines.append(_table(["Skor","Değer"], srows))
        lines.append("")

    # Pedagogy Detay
    if pedagogy:
        lines.append("## Pedagogy Detay")
        praw = pedagogy.get('raw') or {}
        pscores = pedagogy.get('scores') or {}
        counts = (praw.get('counts') or {})
        p_rows = []
        for k,v in counts.items():
            p_rows.append([k, str(v)])
        if p_rows:
            lines.append(_table(["Öğe","Adet"], p_rows))
        lines.append("")
        pr_rows = []
        ratios = praw.get('ratios') or {}
        for k,v in ratios.items():
            pr_rows.append([k, _fmt_score(v)])
        if pr_rows:
            lines.append(_table(["Oran","Değer"], pr_rows))
        lines.append("")
        pscore_rows = []
        for k in ['examples','questions','signposting','definitions','summary','balance_bonus','pedagogy_score']:
            if k in pscores:
                pscore_rows.append([k, _fmt_score(pscores[k])])
        if pscore_rows:
            lines.append(_table(["Skor","Değer"], pscore_rows))
        lines.append("")

    # JSON Ham blok (isteğe bağlı)
    lines.append("## JSON Ham Veri (Kısaltılmış)")
    preview = json.dumps({k: report[k] for k in ['generated_at','source','scoring'] if k in report}, ensure_ascii=False, indent=2)
    lines.append(f"```json\n{preview}\n```")

    return '\n'.join(lines)


def export_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


__all__ = [
    'build_report_data',
    'render_markdown',
    'export_json',
]
"""Rapor üretimi (yer tutucu)
- JSON ve Markdown çıktıları
- PDF opsiyonel (vakit kalırsa)
"""
