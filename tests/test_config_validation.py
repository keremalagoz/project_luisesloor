import os
import tempfile
import yaml

from app.core.config import load_settings, validate_settings


def write_cfg(data):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
    with open(tmp.name, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True)
    return tmp.name


def test_valid_config():
    cfg_data = {
        'weights': {'coverage':0.5,'delivery':0.3,'pedagogy':0.2},
        'metrics': {
            'similarity_thresholds': {'covered':0.8,'partial':0.6},
            'delivery': {'weights': {'wpm':0.2,'filler':0.2,'repetition':0.2,'sentence_length':0.2,'pause':0.2}},
            'pedagogy': {'weights': {'examples':0.2,'questions':0.2,'signposting':0.2,'definitions':0.2,'summary':0.2}},
        },
        'models': {'embedding_model':'text-embedding-004'},
        'app': {'db_path': os.path.join(tempfile.gettempdir(), 'test_db.sqlite')},
    }
    path = write_cfg(cfg_data)
    loaded = load_settings(path=path, force=True)
    ok, errors, warnings = validate_settings(loaded)
    assert ok is True
    assert errors == []


def test_invalid_weights():
    cfg_data = {
        'weights': {'coverage':0.6,'delivery':0.3,'pedagogy':0.3},  # toplam 1.2
        'metrics': {
            'similarity_thresholds': {'covered':0.8,'partial':0.6},
        },
        'models': {'embedding_model':'x'},
    }
    path = write_cfg(cfg_data)
    loaded = load_settings(path=path, force=True)
    ok, errors, warnings = validate_settings(loaded)
    assert ok is False
    assert any('weights' in e for e in errors)


def test_invalid_threshold_order():
    cfg_data = {
        'weights': {'coverage':0.5,'delivery':0.3,'pedagogy':0.2},
        'metrics': {
            'similarity_thresholds': {'covered':0.5,'partial':0.6},  # covered <= partial
        },
        'models': {'embedding_model':'x'},
    }
    path = write_cfg(cfg_data)
    loaded = load_settings(path=path, force=True)
    ok, errors, warnings = validate_settings(loaded)
    assert ok is False
    assert any('covered > partial' in e for e in errors)


def test_missing_embedding_model_warning():
    cfg_data = {
        'weights': {'coverage':0.5,'delivery':0.3,'pedagogy':0.2},
        'metrics': {
            'similarity_thresholds': {'covered':0.8,'partial':0.6},
        },
    }
    path = write_cfg(cfg_data)
    loaded = load_settings(path=path, force=True)
    ok, errors, warnings = validate_settings(loaded)
    # Model yok: warning olmalı, error olmamalı.
    assert ok is True
    assert errors == []
    assert any('embedding_model' in w for w in warnings)
