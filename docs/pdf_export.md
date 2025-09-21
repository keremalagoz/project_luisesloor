# PDF Export

Bu belge PDF rapor üretim özelliğini açıklar.

## Amaç
Analiz sonuçlarının (coverage, delivery, pedagogy ve toplam skor) paylaşılabilir, kurumsal formata yakın PDF çıktısını üretmek.

## Modül
- Konum: `app/core/report_pdf.py`
- Ana Fonksiyon: `export_pdf(report_dict) -> bytes`
- Yardımcı: `generate_pdf_bytes`
- Hata Sınıfı: `PDFReportError`

## Bağımlılık
`reportlab` paketi gereklidir. `requirements.txt` içinde yer alır. Yüklenmemiş ise `PDFReportError` fırlatılır.

## Veri Kaynağı
`app.core.report.build_report_data` fonksiyonunun döndürdüğü sözlük beklenir. Bu yapı aşağıdaki anahtarları içerir:
- `generated_at`
- `source` (filename, stats)
- `modules.coverage / delivery / pedagogy`
- `scoring` (total_score, inputs, weights_used)

## İçerik Yapısı
1. Başlık ve metadata
2. Skor özeti tablosu
3. Coverage ilk 25 topic (topic / status / similarity)
4. Delivery skor tablosu
5. Pedagogy skor tablosu
6. Dipnot (beta ibaresi)

## Sınırlamalar (Beta)
- Trend grafiği yok
- Çok uzun topic listesi ilk 25 ile sınırlandırılır
- Sayfa taşması için ileri kırpma/flow optimizasyonu yapılmadı (normal analiz çıktısı için yeterli)
- Tema / renk paleti minimal

## Geliştirme Fikirleri
- Kapak sayfası (logo, tarih, run id)
- Çok sayfalı otomatik bölümlendirme ve uzun topic listesi paginate
- Trend grafiği embed (matplotlib/altair -> PNG -> Image Flowable)
- İyileşme önerileri (future recommendation engine entegrasyonu)
- Kurumsal renk teması ve tablo zebra stilleri
- HTML'den PDF'e dönüşüm alternatifi (weasyprint) ile stil zenginliği

## Kullanım Örneği
```python
from app.core.report import build_report_data
from app.core.report_pdf import export_pdf

report_dict = build_report_data(source_meta=..., coverage=..., delivery=..., pedagogy=..., scoring=...)
pdf_bytes = export_pdf(report_dict)
with open('rapor.pdf','wb') as f:
    f.write(pdf_bytes)
```

## Test
`tests/test_report_pdf.py` basit bir rapor objesi ile PDF üretip:
- reportlab yüklü değilse hata fırlatma
- yüklüyse bytes > 500 bayt
- dosyaya yazılabilirlik
kontrollerini yapar.

## Sürüm Notu
İlk sürüm minimal fonksiyonellik sunar; görsel zenginleştirme sonraki iterasyonlarda eklenecektir.
