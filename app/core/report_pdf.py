"""PDF rapor üretimi.

Reportlab kullanarak mevcut `report.build_report_data` çıktısından
özet bir PDF oluşturur.

Sadeliği korumak için tek sayfa/çok sayfa otomatik akış ve basit
tablolar kullanılır. Geliştirme fikirleri:
 - Trend grafiği (matplotlib/altair görüntü embed)
 - Kapak sayfası
 - Kurumsal tema / renkler
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - import hatası testi için
    REPORTLAB_AVAILABLE = False


MAX_ROWS_PER_TABLE = 40  # çok uzun tabloları bölme basit eşiği


class PDFReportError(RuntimeError):
    pass


def _kv_table(data: List[Tuple[str, Any]]) -> Table:
    rows = [["Alan", "Değer"]]
    for k, v in data:
        rows.append([k, str(v)])
    tbl = Table(rows, colWidths=[50*mm, 120*mm])
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,0), 4),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ])
    )
    return tbl


def _simple_table(headers: List[str], rows: List[List[Any]]) -> Table:
    tbl_rows = [headers] + [[str(c) for c in r] for r in rows]
    tbl = Table(tbl_rows, repeatRows=1)
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 7),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ])
    )
    return tbl


def generate_pdf_bytes(report: Dict[str, Any]) -> bytes:
    """Verilen rapor dict'inden PDF binary döndür.

    Basit layout:
      - Başlık & meta
      - Skor özeti
      - Coverage tablo (topic-status-sim) (kırpılmış)
      - Delivery skor tablosu
      - Pedagogy skor tablosu
    """
    if not REPORTLAB_AVAILABLE:
        raise PDFReportError("reportlab yüklü değil. requirements.txt içinde olmalı.")

    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    story: List[Any] = []

    def p(txt: str, style="BodyText"):
        story.append(Paragraph(txt, styles[style]))

    # Başlık
    p("<b>Analiz Raporu</b>", style="Title")
    p(f"Üretim: {report.get('generated_at','')}")
    src = report.get('source') or {}
    if src:
        stats = src.get('stats') or {}
        p(f"Kaynak: {src.get('filename','-')} | Kelime: {stats.get('words','-')} | Token~: {stats.get('approx_tokens','-')}")
    story.append(Spacer(1, 6))

    scoring = report.get('scoring') or {}
    inputs = scoring.get('inputs') or {}
    weights = scoring.get('weights_used') or {}
    score_data = [
        ("Coverage", inputs.get('coverage','-')),
        ("Delivery", inputs.get('delivery','-')),
        ("Pedagogy", inputs.get('pedagogy','-')),
        ("Toplam", scoring.get('total_score','-')),
    ]
    p("<b>Skor Özeti</b>", style="Heading2")
    story.append(_kv_table(score_data))
    story.append(Spacer(1, 6))

    if weights:
        p("Ağırlıklar: " + ", ".join(f"{k}={v}" for k,v in weights.items()))
        story.append(Spacer(1,4))

    modules = report.get('modules') or {}
    coverage = modules.get('coverage') or {}
    topics = coverage.get('topics') or []
    if topics:
        p("<b>Coverage (İlk 25)</b>", style="Heading3")
        rows = []
        for t in topics[:25]:
            rows.append([t.get('topic',''), t.get('status',''), f"{t.get('max_similarity') or t.get('similarity'):.2f}" if (t.get('max_similarity') or t.get('similarity')) is not None else '-'])
        story.append(_simple_table(["Topic","Status","Sim"], rows))
        story.append(Spacer(1,6))

    delivery = modules.get('delivery') or {}
    d_scores = (delivery.get('scores') or {})
    if d_scores:
        p("<b>Delivery Skorları</b>", style="Heading3")
        d_rows = [[k, f"{v:.2f}"] for k, v in d_scores.items() if isinstance(v,(int,float))]
        story.append(_simple_table(["Metrik","Skor"], d_rows))
        story.append(Spacer(1,6))

    pedagogy = modules.get('pedagogy') or {}
    p_scores = (pedagogy.get('scores') or {})
    if p_scores:
        p("<b>Pedagogy Skorları</b>", style="Heading3")
        p_rows = [[k, f"{v:.2f}"] for k,v in p_scores.items() if isinstance(v,(int,float))]
        story.append(_simple_table(["Metrik","Skor"], p_rows))
        story.append(Spacer(1,6))

    # Öneriler (opsiyonel)
    recs = report.get('recommendations') or {}
    if recs and isinstance(recs, dict):
        rec_list = recs.get('recommendations') or []
        if rec_list:
            story.append(Spacer(1, 6))
            p("<b>Öneriler (Özet)</b>", style="Heading3")
            rows = []
            for r in rec_list[:12]:
                rows.append([r.get('category',''), r.get('severity',''), r.get('message','')])
            story.append(_simple_table(["Kategori","Önem","Mesaj"], rows))
    # RAG (opsiyonel)
    rag = report.get('rag') or {}
    if rag:
        story.append(Spacer(1, 6))
        p("<b>RAG Özeti</b>", style="Heading3")
        q = rag.get('question') or '-'
        a = (rag.get('answer') or {}).get('answer') if isinstance(rag.get('answer'), dict) else rag.get('answer')
        p(f"Soru: {q}")
        mode = rag.get('retrieval_mode')
        if mode:
            p(f"Retrieval: {mode}")
        if a:
            p("Cevap:")
            p(a[:800])
        srcs = rag.get('sources') or []
        if srcs:
            srows = [[s.get('id',''), f"{(s.get('similarity') or 0):.3f}"] for s in srcs[:10]]
            story.append(_simple_table(["Kaynak ID","Benzerlik"], srows))

    p("Otomatik oluşturulan PDF raporu. Beta sürüm - görsel/grafik henüz ekli değil.")

    doc.build(story)
    return buffer.getvalue()


def export_pdf(report: Dict[str, Any]) -> bytes:
    """Harici API: Rapor dict -> PDF bytes.

    Var olan `app.core.report.export_pdf` yerine kullanılabilir. Geçici olarak
    ana uygulamada bu modülden çağrılacak.
    """
    return generate_pdf_bytes(report)


__all__ = ["export_pdf", "generate_pdf_bytes", "PDFReportError"]
