"""Basit SQLite saklama katmanı.

Tablolar:
  materials: Yüklenen kaynak materyal meta verisi
  runs: Her analiz çalışması (coverage/delivery/pedagogy + toplam)
  topics: Coverage sonucu konu bazlı durumlar
  metrics: Ayrıntılı metrik değerleri (raw + skor)

Not: Şimdilik çok-kullanıcılı eşzamanlı erişim senaryosu hedeflenmiyor.
"""

from __future__ import annotations

import os
import sqlite3
import json
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.path.join("data", "app.db")


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    _ensure_dir(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    cur = conn.cursor()
    # materials
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            size_mb REAL,
            chars INTEGER,
            words INTEGER,
            approx_tokens INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    # runs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            coverage_score REAL,
            delivery_score REAL,
            pedagogy_score REAL,
            total_score REAL,
            weights_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE
        );
        """
    )
    # topics
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            topic TEXT,
            status TEXT,
            similarity REAL,
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );
        """
    )
    # metrics
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            category TEXT,
            name TEXT,
            raw_value REAL,
            score REAL,
            extra_json TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );
        """
    )
    # indeksler (basit)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_material ON runs(material_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_topics_run ON topics(run_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_metrics_run ON metrics(run_id);")
    conn.commit()
    conn.close()


def insert_material(source_meta: Dict[str, Any], db_path: Optional[str] = None) -> int:
    conn = get_connection(db_path)
    cur = conn.cursor()
    stats = source_meta.get("stats", {}) or {}
    cur.execute(
        """
        INSERT INTO materials(filename, size_mb, chars, words, approx_tokens)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            source_meta.get("filename"),
            source_meta.get("size_mb"),
            stats.get("chars"),
            stats.get("words"),
            stats.get("approx_tokens"),
        ),
    )
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid


def insert_run(
    material_id: int,
    scoring: Dict[str, Any],
    coverage: Optional[Dict[str, Any]] = None,
    delivery: Optional[Dict[str, Any]] = None,
    pedagogy: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> int:
    conn = get_connection(db_path)
    cur = conn.cursor()
    coverage_score = (coverage or {}).get("summary", {}).get("coverage_ratio")
    delivery_score = (delivery or {}).get("scores", {}).get("delivery_score")
    pedagogy_score = (pedagogy or {}).get("scores", {}).get("pedagogy_score")
    total_score = scoring.get("total_score") if scoring else None
    weights_json = json.dumps(scoring.get("weights_used")) if scoring else None
    cur.execute(
        """
        INSERT INTO runs(material_id, coverage_score, delivery_score, pedagogy_score, total_score, weights_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            material_id,
            coverage_score,
            delivery_score,
            pedagogy_score,
            total_score,
            weights_json,
        ),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def bulk_insert_topics(run_id: int, coverage: Dict[str, Any], db_path: Optional[str] = None) -> int:
    topics = (coverage or {}).get("topics") or []
    if not topics:
        return 0
    conn = get_connection(db_path)
    cur = conn.cursor()
    rows = [
        (
            run_id,
            t.get("topic"),
            t.get("status"),
            t.get("similarity"),
        )
        for t in topics
    ]
    cur.executemany(
        "INSERT INTO topics(run_id, topic, status, similarity) VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n


def insert_metric(
    run_id: int,
    category: str,
    name: str,
    raw_value: Optional[float],
    score: Optional[float],
    extra: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> int:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO metrics(run_id, category, name, raw_value, score, extra_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            category,
            name,
            raw_value,
            score,
            json.dumps(extra) if extra else None,
        ),
    )
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid


def insert_coverage_metrics(run_id: int, coverage: Dict[str, Any], db_path: Optional[str] = None) -> None:
    if not coverage:
        return
    summary = coverage.get("summary", {})
    for name in ["covered", "partial", "missing"]:
        insert_metric(run_id, "coverage", name, summary.get(name), None, db_path=db_path)
    insert_metric(run_id, "coverage", "coverage_ratio", summary.get("coverage_ratio"), summary.get("coverage_ratio"), db_path=db_path)


def insert_delivery_metrics(run_id: int, delivery: Dict[str, Any], db_path: Optional[str] = None) -> None:
    if not delivery:
        return
    raw = delivery.get("raw", {})
    scores = delivery.get("scores", {})
    for k, v in raw.items():
        if k == "insufficient_data":
            continue
        insert_metric(run_id, "delivery", k, v, scores.get(k), db_path=db_path)
    # toplam skor
    if "delivery_score" in scores:
        insert_metric(run_id, "delivery", "delivery_score", None, scores.get("delivery_score"), db_path=db_path)


def insert_pedagogy_metrics(run_id: int, pedagogy: Dict[str, Any], db_path: Optional[str] = None) -> None:
    if not pedagogy:
        return
    raw = pedagogy.get("raw", {})
    scores = pedagogy.get("scores", {})
    for name, score_val in scores.items():
        if name == "pedagogy_score":
            continue
        # raw karşılığı varsa al
        rv = raw.get(name)
        insert_metric(run_id, "pedagogy", name, rv, score_val, db_path=db_path)
    if "pedagogy_score" in scores:
        insert_metric(run_id, "pedagogy", "pedagogy_score", None, scores.get("pedagogy_score"), db_path=db_path)


def fetch_recent_runs(limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT r.id, r.created_at, m.filename, r.coverage_score, r.delivery_score, r.pedagogy_score, r.total_score
        FROM runs r
        LEFT JOIN materials m ON r.material_id = m.id
        ORDER BY r.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    cols = ["id", "created_at", "filename", "coverage_score", "delivery_score", "pedagogy_score", "total_score"]
    return [dict(zip(cols, row)) for row in rows]


def fetch_run_details(run_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, material_id, coverage_score, delivery_score, pedagogy_score, total_score, weights_json, created_at FROM runs WHERE id=?", (run_id,))
    run_row = cur.fetchone()
    if not run_row:
        conn.close()
        return {}
    cur.execute("SELECT topic, status, similarity FROM topics WHERE run_id=?", (run_id,))
    topics = [
        {"topic": t, "status": s, "similarity": sim}
        for (t, s, sim) in cur.fetchall()
    ]
    cur.execute("SELECT category, name, raw_value, score, extra_json FROM metrics WHERE run_id=?", (run_id,))
    metrics_rows = cur.fetchall()
    metrics = [
        {
            "category": c,
            "name": n,
            "raw_value": rv,
            "score": sc,
            "extra": json.loads(ej) if ej else None,
        }
        for (c, n, rv, sc, ej) in metrics_rows
    ]
    conn.close()
    cols = ["id", "material_id", "coverage_score", "delivery_score", "pedagogy_score", "total_score", "weights_json", "created_at"]
    run_obj = dict(zip(cols, run_row))
    if run_obj.get("weights_json"):
        try:
            run_obj["weights"] = json.loads(run_obj["weights_json"])
        except Exception:
            run_obj["weights"] = None
    run_obj["topics"] = topics
    run_obj["metrics"] = metrics
    return run_obj


__all__ = [
    "init_db",
    "insert_material",
    "insert_run",
    "bulk_insert_topics",
    "insert_metric",
    "insert_coverage_metrics",
    "insert_delivery_metrics",
    "insert_pedagogy_metrics",
    "fetch_recent_runs",
    "fetch_run_details",
    "get_connection",
]
