# Rapor JSON Şeması (Taslak)

```json
{
  "meta": { "lecture_id": "...", "duration_sec": 0, "created_at": "ISO8601" },
  "scores": {
    "coverage": 0,
    "delivery": 0,
    "pedagogy": 0,
    "overall": 0,
    "weights": { "coverage": 0.5, "delivery": 0.3, "pedagogy": 0.2 }
  },
  "coverage": {
    "total_chunks": 0,
    "covered_chunks": 0,
    "partial_chunks": 0,
    "missing_chunks": 0,
    "missing_topics": [
      { "title": "...", "importance": 0.0, "suggestion": "..." }
    ]
  },
  "delivery": {
    "wpm": 0,
    "target_wpm_range": [130,160],
    "filler_rate": 0.0,
    "filler_examples": [],
    "pause_stats": { "count": 0, "avg_ms": 0, "long_pauses": 0 },
    "repetition": { "top_ngrams": [ {"ngram": "...", "count": 0} ] }
  },
  "pedagogy": {
    "clarity": 0,
    "example_density": 0.0,
    "engagement": 0,
    "sequencing": 0,
    "jargon_management": 0,
    "notes": ["..."]
  },
  "progress": {
    "previous_overall": null,
    "delta_overall": null,
    "deteriorated_metrics": [],
    "improved_metrics": []
  },
  "export": {
    "available_formats": ["json","md","pdf"],
    "generated": ["json"]
  },
  "charts_payload": {
    "radar": [
      {"axis":"Coverage","value":0.0},
      {"axis":"Pace","value":0.0},
      {"axis":"Filler Control","value":0.0},
      {"axis":"Repetition","value":0.0},
      {"axis":"Pauses","value":0.0},
      {"axis":"Clarity","value":0.0},
      {"axis":"Engagement","value":0.0}
    ]
  }
}
```

Not: Bu şema hackathon boyunca rafine edilecektir.