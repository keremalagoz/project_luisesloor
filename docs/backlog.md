# Backlog (Gün 1 Taslak)

## Zorunlu (Sprint Hedefi)
- [ ] Upload ekranı (PDF/TXT)
- [ ] Metin çıkarma (PDF → text)
- [ ] Chunking ve embedding (Gemini text-embedding-004)
- [ ] Ses kayıt/upload (tarayıcı → backend çağrısı)
- [ ] Whisper (OpenAI API) ile transkripsiyon
- [ ] Kapsam analizi (cosine similarity)
- [ ] Teslim analizi (WPM, duraklama, filler, tekrar)
- [ ] Pedagojik analiz (açıklık, örnek yoğunluğu, etkileşim, dizgeleme, jargon)
- [ ] Skorlama (Overall = 0.5 COV + 0.3 DEL + 0.2 PED)
- [ ] Rapor üretimi (JSON + Markdown)
- [ ] PDF export (opsiyonel, vakit kalırsa)
- [ ] İlerleme karşılaştırması (SQLite kayıt + trend)
- [ ] Basit dashboard akışı

## Teknik Altyapı
- [ ] `settings.yaml` anahtarları ve threshold’lar
- [ ] Filler kelime listesi (TR+EN) ayarı
- [ ] SQLite şema: `lectures`, `reports`
- [ ] Basit vektör deposu (in-memory)

## Test / Demo
- [ ] Demo PDF seçimi ve etiketleme
- [ ] Demo ses: kasıtlı eksik kavram + filler içeren kayıt
- [ ] Screenflow: Upload → Kayıt → Analiz → Rapor → Export

## Sunum/Pitch
- [ ] Ürün hikâyesi ve farklılaştırıcı noktalar
- [ ] Demo videosu senaryosu

---
Not: Bu liste sprint ilerledikçe güncellenecek.
