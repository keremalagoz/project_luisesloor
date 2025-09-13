# Delivery Manual Test Checklist

Amaç: `compute_delivery_metrics` ve UI Adım 4 çıktılarının tasarlanan normalizasyon kurallarına uygunluğunu doğrulamak.

## 1. Temel Senaryolar
1. Normal hız / düşük filler
   - Transkript: ~200 kelime, filler oranı <%2
   - Süre: 1.3 dakika (≈154 WPM)
   - Beklenti: wpm ~1.0, filler ~1.0, repetition >=0.8, sentence_length ~1.0
2. Çok hızlı konuşma
   - 300 kelime, süre 0.8 dk (≈375 WPM)
   - Beklenti: wpm skoru ~0 (ceza), diğer metrikler uygun ise >0
3. Çok yavaş konuşma
   - 120 kelime, süre 2.0 dk (≈60 WPM)
   - Beklenti: wpm skoru <0.5 (alt banda göre cezalı)
4. Yüksek filler
   - 150 kelime, 30+ filler (≥%20)
   - Beklenti: filler skoru 0
5. Kısa transkript (insufficient)
   - 12–15 kelime
   - Beklenti: tüm alt skorlar 0, `insufficient_data=True`

## 2. Cümle Uzunluğu Kenar Durumları
1. Çok kısa cümleler
   - 100 kelime, 40+ cümle (ortalama <4)
   - Beklenti: sentence_length skoru ~0.3 veya altı
2. Çok uzun cümleler
   - Tek 120+ kelimelik cümle
   - Beklenti: sentence_length skoru ≈0 (yüksek over-penalty)

## 3. Lexical Diversity / Repetition
1. Yüksek çeşitlilik
   - 120 kelime içinde tekrar oranı düşük (benzersiz >70 kelime)
   - Beklenti: repetition (diversity) skoru=1.0 (target ≥0.55)
2. Düşük çeşitlilik
   - 150 kelime: Aynı 10 kelimenin tekrarları
   - Beklenti: diversity ~0.06 → repetition skoru ≈0.1

## 4. Pause Density
1. Az duraklama
   - 200 kelimelik transkript, 0–1 '...' veya boş satır
   - Beklenti: pause skoru ~1.0
2. Aşırı duraklama
   - 150 kelime, 20 '...' (pause density yüksek)
   - Beklenti: pause skoru ≈0

## 5. UI Doğrulamaları (Streamlit)
- Adım 4'e girilen süre 0 ise fallback süre hesaplanıyor mu?
- "Ham Değerler" expander doğru ham metrikleri gösteriyor mu?
- "Kullanılan Konfig" expander config/settings.yaml içindeki delivery değerleri ile uyumlu mu?
- insufficient_data durumunda uyarı bannerı çıkıyor mu?

## 6. Negatif / Boş Girdi Dayanıklılık
1. Boş transkript
   - Beklenti: words=0, insufficient_data=True, skorlar=0
2. Sadece filler kelimeler
   - 25 kelime, %100 filler
   - Beklenti: filler skoru=0, diğer skorlar düşük

## 7. Regresyon Kontrolü
- Aynı transkript + süre ile tekrarlı çalıştırmada skorlar deterministik mi?
- Config değerleri değiştirildiğinde (örneğin ideal_wpm_max=190) wpm skoru farklılaşıyor mu?

## 8. Manuel Hesap Örneği (WPM)
- 180 kelime / 1.2 dk = 150 WPM → ideal aralık (130–170) içinde → wpm skoru 1.0
- 60 kelime / 1 dk = 60 WPM → normalize: (60/130*0.7) ≈ 0.323

## 9. Notlar
- Gözlenen anormallikler için transkript + süre + çıktı JSON'ı kaydedin.
- İyileştirme fikirleri: kısa metinlerde pause density normalizasyonu, min kelime eşiği dinamikleştirme.

---
Hazırlayan: Otomatik oluşturuldu
