from app.core.trends import prepare_run_dataframe, compute_basic_deltas, top_improvements

def build_runs():
    return [
        {'id':1,'total_score':0.50,'coverage_score':0.40,'delivery_score':0.55,'pedagogy_score':0.60},
        {'id':2,'total_score':0.58,'coverage_score':0.50,'delivery_score':0.57,'pedagogy_score':0.62},
        {'id':3,'total_score':0.63,'coverage_score':0.55,'delivery_score':0.59,'pedagogy_score':0.64},
    ]


def test_prepare_dataframe_order():
    runs = build_runs()
    df = prepare_run_dataframe(runs)
    assert list(df['id']) == [1,2,3]

def test_basic_deltas():
    df = prepare_run_dataframe(build_runs())
    d = compute_basic_deltas(df)
    assert d['total_score_delta'] == 0.63 - 0.50
    assert d['coverage_score_delta'] == 0.55 - 0.40

def test_top_improvements():
    df = prepare_run_dataframe(build_runs())
    imp = top_improvements(df, ['total_score','coverage_score','delivery_score','pedagogy_score'])
    assert imp['improved']  # en az bir iyileşme var
    # declined boş olmalı çünkü tüm seriler artıyor
    assert imp['declined'] == []
