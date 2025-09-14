# Rapor Manuel Test Checklist

Bu belge `report.py` modülü (build_report_data, render_markdown, export_json) için manuel doğrulama senaryolarını kapsar.

## 1. Ortam Hazırlığı
- Python sürümü >= 3.10
- Gerekli bağımlılıklar (Streamlit vs.) zaten kurulu olmalı (rapor fonksiyonları ek bağımlılık gerektirmez)
- Çalışma dizini projenin kök klasörü

## 2. Temel Fonksiyon Çağrıları
| Test | Adım | Beklenen |
| ---- | ---- | -------- |
| RPT-01 | build_report_data zorunlu tüm parametrelerle çağır | Dönen dict `generated_at`, `source`, `modules`, `scoring` anahtarlarını içerir |
| RPT-02 | render_markdown(build_report_data(...)) | Markdown başlığı `# Analiz Raporu` ile başlar |
| RPT-03 | export_json(build_report_data(...)) | Geçerli JSON (json.loads başarır), newline ile biter |

## 3. Coverage Yalnız Senaryosu
- delivery=None, pedagogy=None ver.
- Beklenen: Markdown içinde sadece Coverage ve Skor Özeti (delivery/pedagogy yok), toplam skor coverage skoruna eşit.

## 4. Delivery Yalnız Senaryosu
- coverage=None, pedagogy=None
- Beklenen: Coverage tablosu yok, delivery bölümü var, toplam skor delivery skoruna eşit.

## 5. Pedagogy Yalnız Senaryosu
- coverage=None, delivery=None
- Beklenen: Sadece pedagogy ve skor özeti.

## 6. Tümü Var (Tam Senaryo)
- Örnek: scripts/test_report.py içindeki mock veriler.
- Beklenen: Üç modül tablo ve skor satırları doğru; Toplam skor ağırlıklarla uyumlu.

## 7. Aşırı / Kenar Değerler
| Test | Durum | Beklenen |
| ---- | ----- | -------- |
| RPT-07 | coverage_ratio=0.0 | Toplam skor düşer, ratio 0.00 yazılır |
| RPT-08 | coverage_ratio=1.0 | Ratio 1.00 yazılır |
| RPT-09 | delivery_score=0.0 | Delivery satırı 0.00 |
| RPT-10 | pedagogy_score=1.0 | Pedagogy satırı 1.00 |
| RPT-11 | Çok uzun topic listesi (>30) | Markdown tabloda satırlar oluşturulur, çökmez |

## 8. Biçim Kontrolleri
- Markdown tablolarında başlık ayırıcı satır (`| --- |`) her tabloda var.
- Yüzen sayılar iki ondalık (format: f"{x:.2f}").
- JSON `generated_at` ISO8601 + 'Z'.

## 9. Hata Dayanımı
| Test | Manipülasyon | Beklenen |
| ---- | ------------ | -------- |
| RPT-12 | summary içinden bir alanı (covered) çıkar | build_report_data yine de dict döner, eksik alanlar KeyError üretmemeli (gerekirse mock'ta alan zorunlu kılınır) |
| RPT-13 | delivery scores içinde beklenmeyen ek anahtar | Markdown render hata vermez, ekstra anahtar görmezden gelinir |

(Not: Şu anki implementasyon kritik alan yoksa KeyError üretebilir; bu testler ileride esnekliğe dönük.)

## 10. Performans (Elle)
- 100 topic + 500 satır transcript özeti simüle et → build_report_data & render_markdown toplam < 200 ms (yerel ölçüm, time.perf_counter).

## 11. Reprodüksiyon Adımları (Tam Senaryo)
1. `python scripts/test_report.py` çalıştır.
2. Konsolda JSON ilk 300 char ve ilk 40 satır markdown görünür.
3. Satır sayısı ~90+ olmalı (topic sayısına bağlı değişebilir).

## 12. Manuel Doğrulama Checklist
- [ ] Başlık doğru
- [ ] Tarih ISO format
- [ ] Skor tablosu 4 satır (modüller + toplam) mevcut modüllere göre
- [ ] Coverage summary satırı (Covered/Partial/Missing/Ratio)
- [ ] Delivery ham metrik tablosu
- [ ] Delivery skor tablosu
- [ ] Pedagogy counts & ratios tabloları (varsa)
- [ ] Pedagogy skor tablosu + balance_bonus (varsa)
- [ ] Float formatları iki ondalık
- [ ] JSON parse edilebilir

## 13. Gelecek Geliştirmeler İçin Notlar
- PDF üretimi sonrası ek test: PDF dosya boyutu > 0, belirli bir regex ile başlık doğrulama (metin çıkartma aracı ile)
- Lokalizasyon desteği (TR/EN switch) → yeni test senaryoları
- Rapor versiyon alanı eklenmeli (schema evrimi için)

---
Bu doküman yeni rapor özellikleri eklendikçe güncellenmelidir.
