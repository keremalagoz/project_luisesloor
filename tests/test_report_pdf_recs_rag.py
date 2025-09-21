from app.core.report import build_report_data
from app.core.report_pdf import export_pdf, REPORTLAB_AVAILABLE, PDFReportError


def _sample_report_with_recs_rag():
    base = build_report_data(
        source_meta={"filename":"demo.txt","stats":{"words":120,"approx_tokens":150}},
        coverage={"summary":{"coverage_ratio":0.75},"topics":[{"topic":"Giriş","status":"covered","max_similarity":0.9}]},
        delivery={"scores":{"delivery_score":0.62,"wpm":0.5},"raw":{}},
        pedagogy={"scores":{"pedagogy_score":0.55,"examples":0.4},"raw":{}},
        scoring={"total_score":0.64,"inputs":{"coverage":0.75,"delivery":0.62,"pedagogy":0.55},"weights_used":{"coverage":0.5,"delivery":0.3,"pedagogy":0.2}},
    )
    base["recommendations"] = {
        "recommendations": [
            {"category":"coverage","severity":"high","message":"Eksik konuları tamamlayın.","rationale":"","meta":{}},
            {"category":"delivery","severity":"medium","message":"Konuşma hızını optimize edin.","rationale":"","meta":{}}
        ],
        "summary": {"counts":{"high":1,"medium":1,"low":0},"total":2}
    }
    base["rag"] = {
        "question": "Ana konu nedir?",
        "answer": {"answer":"Makine öğrenmesine giriş.", "mode":"extractive", "sources":[{"id":"c1","similarity":0.82}], "confidence":0.82},
        "sources": [{"id":"c1","similarity":0.82},{"id":"c3","similarity":0.71}]
    }
    return base


def test_pdf_with_recs_and_rag(tmp_path):
    rpt = _sample_report_with_recs_rag()
    if not REPORTLAB_AVAILABLE:
        try:
            export_pdf(rpt)
        except PDFReportError:
            return
        raise AssertionError("reportlab yokken PDFReportError beklenirdi")
    pdf_bytes = export_pdf(rpt)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 500
    out = tmp_path / "rapor_recs_rag.pdf"
    out.write_bytes(pdf_bytes)
    assert out.exists() and out.stat().st_size == len(pdf_bytes)
