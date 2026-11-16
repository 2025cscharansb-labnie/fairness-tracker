from app.fairness import analyze_fairness


def test_equal_work_is_fully_fair():
    stats = {"alice": {"score": 10}, "bob": {"score": 10}}
    result = analyze_fairness(stats)
    assert result["fairness_score"] == 100
    assert result["flags"] == []


def test_uneven_work_is_flagged():
    stats = {"alice": {"score": 90}, "bob": {"score": 10}}
    result = analyze_fairness(stats)
    assert result["fairness_score"] == 20
    assert len(result["flags"]) == 2


def test_empty_stats():
    result = analyze_fairness({})
    assert result["fairness_score"] == 0