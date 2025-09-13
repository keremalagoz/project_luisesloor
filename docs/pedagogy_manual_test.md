# Pedagogy Manual Test Checklist

Amaç: `compute_pedagogy_metrics` fonksiyonu ve UI Adım 5 çıktılarının hedef oran & normalizasyon kurallarına uygunluğunu doğrulamak.

## 1. Eşik / Yetersiz Veri
1. Cümle sayısı < 10 → tüm skorlar 0, `insufficient_data=True`.
2. Tam 10 cümle → değerlendirme başlar (örnek ↔ insufficient sınırı).

## 2. Tek Metrik Baskın (Aşırı) Senaryolar
1. Aşırı örnek (her cümlenin örnek olması). 10 cümle / 10 örnek.
   - examples ratio = 1.0 (>2*target? target=0.15 → 2*target=0.30 → çok üzerinde)
   - Beklenen: examples skoru aşırı-penalty ile ≈0.6
2. Aşırı definitions (her cümlede “nedir”).
   - definitions ratio ≈1.0 → skor ≈0.6
3. Aşırı signposting (her cümlenin başı yönlendirme). → signposting skoru ≈0.6

## 3. Dengeli Yüksek Senaryo
- 12–14 cümle, her metrik hedefin biraz üstünde fakat 2x target altı.
- Her skor ≈1.0, std < 0.25 → balance_bonus = 0.05 → pedagogy_score cap 1.0.

## 4. Sorular
- “neden”, “nasıl”, “hangi”, “?” içerikle 10 cümlede 2 soru → questions ratio = 0.2 → plateau (1.0) + no penalty (≤2x target).

## 5. Summary / Recap
- Transkript sonuna 2–3 özet cümlesi (“özetle”, “toparlarsak”, “sonuç olarak”).
- ratio > target (0.04) fakat ≤2*target (0.08) ise skor=1.0.
- 0.15’e çıkarsa penalty bölgesine ( >2*target ) düşer → ~0.6 civarına iner.

## 6. Balance Bonus
- Tek metrik yüksek (diğerleri 0) → std yüksek → bonus 0.
- Tüm metrikler 0 → bonus 0.
- Çoğu 0.8–1.0 bandında → std düşük → bonus 0.05 eklenir.

## 7. UI Kontrolleri
- Adım 5’te “Pedagogy Hesapla” sonrası skor kartları doğru güncelleniyor mu?
- "Ham Sayımlar / Oranlar" expander içerikleri counts & ratios ile eşleşiyor mu?
- insufficient_data durumunda uyarı var mı?
- Konfig expander içeriği `settings.yaml` pedagogy bloklarıyla uyumlu mu?

## 8. Determinizm
- Aynı transkript tekrar çalıştırıldığında aynı skorları veriyor mu?
- Config hedefleri değiştirilip (ör: examples target 0.20) skor değişimi beklenen doğrultuda mı (daha zor 1.0’a ulaşmalı)?

## 9. Kenar Durumlar
- Boş string → insufficient + skorlar 0.
- Noktalama olmayan uzun paragraf (tek cümle algısı) → cümle sayısı 1 → insufficient.
- Yalnızca “?” işaretleri ile biten kısa cümleler (>=10) → questions skoru 1.0, diğerleri 0, pedagogy_score düşük (balance_bonus yok).

## 10. Manuel Kontrol Örnek Hesap
Örnek ratio = 0.20, target=0.15 → 0.20 ≤ 2*0.15 (=0.30) → skor 1.0.
Signposting ratio = 0.50, target=0.18 → 2*target=0.36 < 0.50 → excess=0.50-0.36=0.14
penalty = min(0.4, 0.14 / (0.36)) ≈ 0.389 → skor ≈ 0.611 (test scriptindeki değere yakın olmalı).

---
Hazırlayan: Otomatik oluşturuldu
