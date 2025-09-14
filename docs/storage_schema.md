## Veritabanı Şeması ve Saklama Katmanı

Bu belge `app/core/storage.py` içinde tanımlanan SQLite tabanlı kalıcı saklama katmanını açıklar.

### Genel Amaç
Analiz edilen her materyal ve ona bağlı skor çıktıları (coverage / delivery / pedagogy) ile her bir alt metrik değerinin kalıcı olarak saklanması ve geçmiş çalışmalara hızlıca erişim.

### Tablolar

1. materials
   - `id` INTEGER PK
   - `filename` TEXT
   - `size_mb` REAL
   - `chars` INTEGER
   - `words` INTEGER
   - `approx_tokens` INTEGER
   - `created_at` TIMESTAMP (varsayılan CURRENT_TIMESTAMP)

2. runs
   - `id` INTEGER PK
   - `material_id` INTEGER FK -> materials.id (CASCADE)
   - `coverage_score` REAL (coverage_ratio)
   - `delivery_score` REAL (delivery toplam skor)
   - `pedagogy_score` REAL (pedagogy toplam skor)
   - `total_score` REAL (ağırlıklı genel)
   - `weights_json` TEXT (kullanılan ağırlıkların JSON string'i)
   - `created_at` TIMESTAMP

3. topics
   - `id` INTEGER PK
   - `run_id` INTEGER FK -> runs.id (CASCADE)
   - `topic` TEXT
   - `status` TEXT (`covered|partial|missing`)
   - `similarity` REAL

4. metrics
   - `id` INTEGER PK
   - `run_id` INTEGER FK -> runs.id (CASCADE)
   - `category` TEXT (`coverage|delivery|pedagogy` vs.)
   - `name` TEXT (ör: wpm, filler, examples, coverage_ratio ...)
   - `raw_value` REAL (ham değer veya count; bazı skorlar için None)
   - `score` REAL (normalize edilmiş 0–1 arası değer; coverage alt sayımlarda None olabilir)
   - `extra_json` TEXT (ileride genişletme amaçlı JSON)

### Indeksler
Performans için minimal indeksler eklendi:
- `idx_runs_material` (runs.material_id)
- `idx_topics_run` (topics.run_id)
- `idx_metrics_run` (metrics.run_id)

### Temel Fonksiyonlar
- `init_db(db_path=None)` : Şema oluşturur.
- `insert_material(source_meta, db_path=None)` : materials kaydı döner material_id.
- `insert_run(material_id, scoring, coverage, delivery, pedagogy, db_path=None)` : run kaydı döner run_id.
- `bulk_insert_topics(run_id, coverage)` : coverage topics listesini ekler.
- `insert_coverage_metrics(run_id, coverage)` : coverage özet metriklerini ekler.
- `insert_delivery_metrics(run_id, delivery)` : delivery ham + skor metrikleri.
- `insert_pedagogy_metrics(run_id, pedagogy)` : pedagogy skor alt detayları.
- `fetch_recent_runs(limit=10)` : Son N run (id, filename, kısmi skorlar).
- `fetch_run_details(run_id)` : Run + topics + metrics birleşik obje.

### Kullanım Akışı (UI Step 6)
1. Analiz skorları hesaplandıktan sonra kullanıcı "Run Kaydet" butonuna basar.
2. `init_db` çağrısı (gerekirse) -> `insert_material` -> `insert_run`.
3. Coverage/Delivery/Pedagogy objeleri varsa ilgili toplu ve detay metrik ekleme fonksiyonları çağrılır.
4. `last_run_id` sessionState'e yazılır ve kullanıcıya gösterilir.
5. `fetch_recent_runs` tablo görünümü ile hızlı geçmiş listesi sunulur.

### Tasarım Notları
- Şimdilik versiyonlama yok; ileride `schema_version` tablosu eklenebilir.
- `extra_json` sütunu ileride karmaşık metrik detayları veya model versiyonlarını saklamak için yer tutucu.
- Concurrency düşük öncelik; yoğun paralel kullanım için connection havuzu + WAL modu değerlendirilebilir.
- Büyük metin gövdeleri kaydedilmiyor; yalnızca özet istatistikler saklanıyor (disk şişmesini azaltma hedefi).

### Gelecek İyileştirmeler
- Migration helper (schema upgrade).
- Run silme / temizlik komutları.
- Filtreleme (tarih, skor aralıkları) ve arama.
- Material'e ait birden çok transcript varyantı desteği.
- Analiz parametreleri (ayarlanan threshold ve konfig) için ayrı bir param tablosu.

### Hızlı Örnek (Kod)
```python
from app.core import storage

storage.init_db()
mid = storage.insert_material({'filename':'x.pdf','size_mb':1.2,'stats':{'chars':2000,'words':400,'approx_tokens':500}})
rid = storage.insert_run(mid, scoring_obj, coverage=cov_obj, delivery=del_obj, pedagogy=ped_obj)
storage.insert_delivery_metrics(rid, del_obj)
recent = storage.fetch_recent_runs()
detail = storage.fetch_run_details(rid)
```

### Sık Karşılaşılabilecek Sorular
S: DB dosyası nerede?
> `config/settings.yaml` içinde `app.db_path` ile tanımlı; varsayılan `data/app.db`.

S: Aynı materyali tekrar kaydedersem ne olur?
> Yeni bir run satırı oluşur; materials tablosunda duplicate satır tutulmuş olur. İleride uniq hash ile birleştirme eklenebilir.

S: Büyük metinleri neden saklamıyoruz?
> Şimdilik performans ve depolama maliyetini düşük tutmak için sadece özet istatistik saklanıyor. İleride opsiyonel blob alanı eklenebilir.
