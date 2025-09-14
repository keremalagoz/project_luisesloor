# Trend & Progress Dashboard

Bu bölüm, run geçmişi üzerinden skorların zaman içindeki değişimini görselleştirir.

## Özellikler (MVP)
- Toplam, Coverage, Delivery, Pedagogy skor serileri çizgi grafiği.
- İlk ve son run arasındaki delta metrik kutuları.
- En çok iyileşen ve gerileyen metrikler listesi.
- Run sayısı (N) seçimi.
- Skor tablosu (ID + skor kolonları).

## Veri Kaynağı
`storage.fetch_recent_runs()` sonuçları DataFrame'e dönüştürülür. `created_at` varsa kronolojik sıralama için kullanılır; yoksa `id` artışına göre.

## Fonksiyonlar
`prepare_run_dataframe(runs)` → DataFrame
`compute_basic_deltas(df)` → {total_score_delta, ...}
`top_improvements(df, metric_cols)` → {'improved':[(metrik,delta)], 'declined':[(metrik,delta)]}

## Edge Cases
- <2 run: Trend çizilmez, uyarı gösterilir.
- Eksik skor: İlgili kolon DataFrame'de NaN olarak kalır; delta None dönebilir.

## Genişletme Önerileri
1. Alt metrik trendleri (ör. filler_score, examples vb.).
2. Rolling average (pencere=3) ile smoothing.
3. Hedef çizgisi overlay (örn. coverage >=0.75).
4. İleri analiz: Momentum / son n run eğimi.
5. PDF rapor entegrasyonu (trend grafiğini görüntü export).

## Testler
`tests/test_trends.py` temel doğrulamalar:
- Sıra koruması
- Delta hesapları
- Tüm seriler artınca declined boş olması

---
Bu MVP, pedagojik ilerleme hikayesini görsel hale getirerek kullanıcı değer algısını artırır.
