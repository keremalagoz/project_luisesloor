from app.core.recommendations import generate_recommendations

def test_recommendations_low_coverage():
    coverage = {
        'summary': {'coverage_ratio': 0.42},
        'topics': [
            {'topic':'Giriş','status':'missing','max_similarity':0.1},
            {'topic':'Örnekler','status':'partial','max_similarity':0.5},
        ]
    }
    recs = generate_recommendations(coverage=coverage)
    cats = [r['category'] for r in recs['recommendations']]
    assert 'coverage' in cats
    assert recs['summary']['total'] >= 2


def test_recommendations_delivery_flags():
    delivery = {
        'scores': {
            'wpm': 0.40,
            'filler': 0.30,
            'repetition': 0.45,
            'sentence_length': 0.52,
            'pause': 0.49,
            'delivery_score': 0.44
        },
        'raw': {}
    }
    recs = generate_recommendations(delivery=delivery)
    # wpm, filler, repetition, pause en azından bazı öneriler üretmeli
    assert any(r['category']=='delivery' for r in recs['recommendations'])


def test_recommendations_pedagogy_and_overall():
    pedagogy = {
        'scores': {
            'examples': 0.40,
            'questions': 0.80,
            'signposting': 0.55,
            'definitions': 0.35,
            'summary': 0.90,
            'balance_bonus': 0.70,
            'pedagogy_score': 0.60
        },
        'raw': { 'counts': {}, 'ratios': {} }
    }
    scoring = { 'total_score': 0.58 }
    recs = generate_recommendations(pedagogy=pedagogy, scoring=scoring)
    cats = {r['category'] for r in recs['recommendations']}
    assert 'pedagogy' in cats
    assert 'overall' in cats


def test_recommendations_good_scores_minimal():
    coverage = {'summary': {'coverage_ratio': 0.90}, 'topics': []}
    delivery = {'scores': {'wpm':0.85,'filler':0.88,'repetition':0.90,'sentence_length':0.92,'pause':0.87,'delivery_score':0.89}, 'raw':{}}
    pedagogy = {'scores': {'examples':0.82,'questions':0.80,'signposting':0.83,'definitions':0.81,'summary':0.90,'balance_bonus':0.85,'pedagogy_score':0.85}, 'raw':{'counts':{},'ratios':{}}}
    scoring = {'total_score':0.86}
    recs = generate_recommendations(coverage, delivery, pedagogy, scoring)
    # yüksek skorlar -> ya sıfır ya da sadece düşük öncelikli birkaç öneri
    assert recs['summary']['total'] <= 3
