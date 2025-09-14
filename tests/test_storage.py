import os
import tempfile
from app.core import storage


def test_storage_lifecycle():
    # Geçici veritabanı
    fd, tmp = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        storage.init_db(tmp)
        # Material ekle
        mid = storage.insert_material({
            'filename': 'doc.txt',
            'size_mb': 0.12,
            'stats': {'chars': 1200, 'words': 250, 'approx_tokens': 300}
        }, db_path=tmp)
        assert mid > 0
        # Run ekle (coverage yok)
        scoring = {'total_score': 0.75, 'weights_used': {'coverage':0.5,'delivery':0.3,'pedagogy':0.2}}
        rid = storage.insert_run(mid, scoring, coverage=None, delivery=None, pedagogy=None, db_path=tmp)
        assert rid > 0
        # Coverage ekle (örnek)
        coverage = {
            'summary': {'covered':2,'partial':1,'missing':1,'coverage_ratio':0.5},
            'topics': [
                {'topic':'A','status':'covered','similarity':0.9},
                {'topic':'B','status':'partial','similarity':0.7},
            ]
        }
        storage.bulk_insert_topics(rid, coverage, db_path=tmp)
        storage.insert_coverage_metrics(rid, coverage, db_path=tmp)
        # Delivery ekle
        delivery = {
            'raw': {'wpm':150,'filler_ratio':0.03,'lexical_diversity':0.6,'avg_sentence_length':14,'pause_ratio':0.05,'insufficient_data':False},
            'scores': {'wpm':0.8,'filler':0.9,'repetition':0.7,'sentence_length':0.85,'pause':0.9,'delivery_score':0.83}
        }
        storage.insert_delivery_metrics(rid, delivery, db_path=tmp)
        # Pedagogy ekle
        pedagogy = {
            'raw': {'examples':3,'questions':2,'signposting':4,'definitions':1,'summary':1,'insufficient_data':False},
            'scores': {'examples':0.7,'questions':0.6,'signposting':0.8,'definitions':0.5,'summary':0.6,'balance_bonus':0.1,'pedagogy_score':0.66}
        }
        storage.insert_pedagogy_metrics(rid, pedagogy, db_path=tmp)
        # Recent
        recent = storage.fetch_recent_runs(limit=5, db_path=tmp)
        assert any(r['id']==rid for r in recent)
        # Detail
        detail = storage.fetch_run_details(rid, db_path=tmp)
        assert detail['id'] == rid
        assert len(detail['topics']) == 2
        cat_names = {(m['category'], m['name']) for m in detail['metrics']}
        assert ('coverage','coverage_ratio') in cat_names
        assert ('delivery','delivery_score') in cat_names
        assert ('pedagogy','pedagogy_score') in cat_names
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
