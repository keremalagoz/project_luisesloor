## Run History ve Karşılaştırma Özelliği

Bu özellik, kaydedilmiş analiz çalışmalarını (run) görüntülemenizi ve iki farklı run arasındaki metrik farklarını incelemenizi sağlar.

### Nerede?
Streamlit arayüzünde Step 6 (Genel Skor Dashboard) altında `Run History ve Karşılaştırma` bölümü.

### Nasıl Çalışır?
1. Önce bir çalışmayı kaydetmek için Step 6'da `Run Kaydet` butonuna basmanız gerekir.
2. Kaydedilen run kayıtları `data/app.db` içinde saklanır (konfig `config/settings.yaml` > `app.db_path`).
3. `Son Run Listesi` expander'ı son N run (varsayılan fetch fonksiyonunda limit=10) listesini gösterir.
4. `Run Seç (A)` ile bir run seçilir. Opsiyonel olarak `Karşılaştır (B)` alanından ikinci bir run seçilebilir.
5. `Run Detay Yükle` tıklandığında A (ve varsa B) run detayları çekilir ve metrikler görüntülenir.

### Gösterilen Bilgiler
- Run A Detayları: Tüm kaydedilmiş metrik satırları (category, name, raw_value, score)
- Coverage Topics: Coverage analizi varsa her topic için durum ve similarity
- Karşılaştırma (A vs B):
  - Özet kartları: Toplam Skor A, Toplam Skor B, Delta, İyileşen, Gerileyen
  - Metrik Delta Tablosu: category/name bazında A skoru, B skoru, delta ve trend (↑, ↓, →)

### Delta Hesaplama Mantığı
`app/core/history.py` içindeki `compare_runs` fonksiyonu:
- Sadece hem A hem B tarafında bulunan (category, name) çiftlerini dahil eder.
- Her metrik için `delta = score_b - score_a`.
- direction:
  - `up` (delta > 0)
  - `down` (delta < 0)
  - `flat` (|delta| < 1e-9)
- Özet alanları: improved/declined/unchanged sayıları, ortalama delta, toplam skor farkı.

### Kısıtlar & Notlar
- Şimdilik sadece `score` alanı numeric olan metrikler kıyaslanır (coverage alt sayımları ham count olarak eklenmişse ve skor None ise karşılaştırmaya girmez).
- Bir run yalnızca seçilip B boş bırakılırsa karşılaştırma tablosu gösterilmez, sadece Run A detayları gösterilir.
- Performans: Tekil run fetch işlemleri küçük olduğundan ek optimizasyon gerekmemektedir. Büyük ölçek ihtiyaçlarında pagination veya limit parametreleri eklenebilir.

### Gelecek İyileştirme Fikirleri
- Tarih aralığı ve skor filtresi
- Karşılaştırma grafikleri (ör. sparkline, bar delta)
- Export: Seçilen iki run için karşılaştırma raporu (Markdown/JSON)
- “Favori” run işaretleme ve hızlı erişim
- Metrik kategorisi filtrelemesi

### Örnek Kullanım (Kod)
```python
from app.core import storage
from app.core.history import compare_runs

db_path = 'data/app.db'
run_a = storage.fetch_run_details(12, db_path=db_path)
run_b = storage.fetch_run_details(15, db_path=db_path)
cmp = compare_runs(run_a, run_b)
print(cmp['summary'])
for row in cmp['metrics']:
    print(row['category'], row['name'], row['delta'], row['direction'])
```

### Test
`tests/test_compare.py` temel delta ve yön sınıflandırmasını doğrular; sadece B'de olan metriklerin hariç bırakıldığını ve summary istatistiklerini kontrol eder.

---
Bu doküman yeni karşılaştırma görselleştirme veya export özellikleri eklendikçe güncellenecektir.
