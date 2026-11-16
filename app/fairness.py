def gini(values):
    """Inequality measure: 0 = perfectly equal, 1 = one person did everything."""
    n = len(values)
    total = sum(values)
    if n < 2 or total == 0:
        return 0.0
    ordered = sorted(values)
    weighted = sum((i + 1) * v for i, v in enumerate(ordered))
    raw = (2 * weighted) / (n * total) - (n + 1) / n
    return raw * n / (n - 1)  # scale so the maximum is exactly 1


def analyze_fairness(stats):
    """Take the output of score_contributors and judge how fair the split was."""
    if not stats:
        return {"fairness_score": 0, "shares": {}, "flags": ["No contributions found"]}

    scores = {name: data["score"] for name, data in stats.items()}
    total = sum(scores.values())
    n = len(scores)

    if total == 0:
        return {"fairness_score": 0, "shares": {}, "flags": ["No meaningful contributions found"]}

    shares = {name: round(score / total * 100, 1) for name, score in scores.items()}
    fair_share = round(100 / n, 1)

    flags = []
    if n == 1:
        flags.append("Only one contributor found")
    else:
        for name, share in shares.items():
            if share > fair_share * 1.5:
                flags.append(f"{name} did {share}% of the work (fair share is {fair_share}%)")
            elif share < fair_share * 0.5:
                flags.append(f"{name} did only {share}% of the work (fair share is {fair_share}%)")

    fairness_score = round((1 - gini(list(scores.values()))) * 100)
    return {"fairness_score": fairness_score, "shares": shares, "flags": flags}