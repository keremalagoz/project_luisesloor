# Öneri Motoru (Recommendation Engine)

Bu modül analiz edilen üç ana alan (Coverage, Delivery, Pedagogy) ve toplam skor üzerinden kural tabanlı öneriler üretir.

## Konum
`app/core/recommendations.py`

## Ana Fonksiyon
```python
generate_recommendations(coverage=None, delivery=None, pedagogy=None, scoring=None, max_recs=25) -> dict
```

## Çıktı Yapısı
```json
{
  "recommendations": [
    {
      "category": "coverage|delivery|pedagogy|overall",
      "severity": "high|medium|low",
      "message": "...",
      "rationale": "...",
      "meta": { /* ek veri */ }
    }
  ],
  "summary": {
    "counts": {"high": n, "medium": n, "low": n},
    "total": n
  }
}
```

## Heuristik Kurallar
### Coverage
- `coverage_ratio < 0.50` => yüksek öncelik iyileştirme
- `0.50 <= coverage_ratio < 0.75` => orta öncelik
- Eksik konu sayısı > 0 => high severity öneri (ilk 10 konu meta)
- Partial konu sayısı > 0 => medium severity öneri (ilk 10 konu meta)

### Delivery (scores)
- WPM skoru düşük / orta ise hız optimizasyonu
- Filler skoru düşükse filler azaltma
- Repetition skoru düşük/orta ise çeşitlendirme
- Sentence length skoru düşük/orta ise sadeleştirme/denge
- Pause skoru düşük/orta ise anlamlı duraklama ekleme
- `raw.insufficient_data` => high severity uyarı

### Pedagogy
- examples, questions, signposting, definitions, summary skorları için aynı eşikler (0.75 / 0.50)
- Her düşük/orta skor için ilgili yönlendirme mesajı
- `raw.insufficient_data` => high severity

### Overall
- Toplam skor < 0.50 => high "genel düşük" önerisi
- 0.50–0.75 => medium iyileştirme önerisi

## Öncelik Sıralaması
Öneriler severity (high > medium > low) ve kategori adına göre sıralanır. `max_recs` ile kırpılır (varsayılan 25).

## Severity Eşikleri
- Skor >= 0.75 => düşük öncelik (low) – iyi seviye
- 0.50–0.75 => medium
- < 0.50 => high

## Genişletme Fikirleri
- Ağırlıklandırılmış öneri puanı (impact * confidence)
- Kullanıcı aksiyon takibi (uygulandı / ertele)
- LLM ile natural language “coaching paragraph” üretimi
- Trend analizi bağlamında koşullu öneri (ör: son 5 run azalan metrik)
- PDF rapora yüksek öncelik önerilerinin ek ve sayfa numarası linklenmesi

## Testler
`tests/test_recommendations.py` aşağıdaki senaryoları kapsar:
- Düşük coverage -> birden çok coverage önerisi
- Delivery metrikleri zayıf -> delivery önerileri
- Pedagogy+kısmen düşük toplam skor -> pedagogy & overall önerileri
- Yüksek skorlar -> öneri sayısı minimal

## Sürüm
İlk sürüm (beta): kural seti basit ve deterministik.
