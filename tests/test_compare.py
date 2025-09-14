from app.core.history import compare_runs


def _mock_run(total: float, metrics):
    return {
        'id': 1,
        'total_score': total,
        'metrics': metrics,
    }


def test_compare_basic_delta():
    run_a = _mock_run(0.70, [
        {'category':'delivery','name':'wpm','score':0.60},
        {'category':'delivery','name':'filler','score':0.80},
        {'category':'pedagogy','name':'examples','score':0.50},
    ])
    run_b = _mock_run(0.80, [
        {'category':'delivery','name':'wpm','score':0.75},
        {'category':'delivery','name':'filler','score':0.70},  # düşüş
        {'category':'pedagogy','name':'examples','score':0.50},  # aynı
        {'category':'pedagogy','name':'summary','score':0.90},   # ekstra (run_a'da yok, hariç)
    ])
    cmp = compare_runs(run_a, run_b)
    rows = { (r['category'], r['name']): r for r in cmp['metrics'] }
    assert ('delivery','wpm') in rows
    assert ('delivery','filler') in rows
    assert ('pedagogy','examples') in rows
    # extra metric (summary) sadece B'de: karşılaştırmaya dahil edilmemeli
    assert ('pedagogy','summary') not in rows
    # Delta kontrol
    assert abs(rows[('delivery','wpm')]['delta'] - 0.15) < 1e-9
    assert rows[('delivery','filler')]['direction'] == 'down'
    assert rows[('pedagogy','examples')]['direction'] == 'flat'
    # Summary
    summary = cmp['summary']
    assert summary['count_improved'] == 1
    assert summary['count_declined'] == 1
    assert summary['count_unchanged'] == 1
    assert abs(summary['total_score_delta'] - 0.10) < 1e-9
