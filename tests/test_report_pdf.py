import os
from app.core.report import build_report_data
from app.core.report_pdf import export_pdf, PDFReportError, REPORTLAB_AVAILABLE


def _sample_report():
    return build_report_data(
        source_meta={"filename":"demo.txt","stats":{"words":120,"approx_tokens":150}},
        coverage={"summary":{"coverage_ratio":0.75},"topics":[{"topic":"Giriş","status":"covered","max_similarity":0.9}]},
        delivery={"scores":{"delivery_score":0.62,"wpm":0.5},"raw":{}},
        pedagogy={"scores":{"pedagogy_score":0.55,"examples":0.4},"raw":{}},
        scoring={"total_score":0.64,"inputs":{"coverage":0.75,"delivery":0.62,"pedagogy":0.55},"weights_used":{"coverage":0.5,"delivery":0.3,"pedagogy":0.2}},
    )


def test_pdf_generation_basic(tmp_path):
    report = _sample_report()
    if not REPORTLAB_AVAILABLE:
        # reportlab yoksa belirli hata beklenir
        try:
            export_pdf(report)
        except PDFReportError:
            return
        raise AssertionError("REPORTLAB_AVAILABLE False iken PDFReportError atılmalıydı")
    else:
        pdf_bytes = export_pdf(report)
        assert isinstance(pdf_bytes, (bytes, bytearray))
        assert len(pdf_bytes) > 500  # minimal boyut
        out_file = tmp_path / "rapor.pdf"
        out_file.write_bytes(pdf_bytes)
        assert out_file.exists() and out_file.stat().st_size == len(pdf_bytes)
