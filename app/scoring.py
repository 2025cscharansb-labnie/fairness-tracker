WEIGHTS = {"commit": 1, "pr_opened": 2, "pr_merged": 3, "review": 2}

TRIVIAL_MESSAGES = {"update", "fix", "test", "commit", "changes", "."}


def is_meaningful_commit(message):
    """Ignore merge commits and trivial one-word commits."""
    first_line = message.strip().split("\n")[0].strip().lower()
    if first_line.startswith("merge"):
        return False
    if len(first_line) < 5 or first_line in TRIVIAL_MESSAGES:
        return False
    return True


def score_contributors(commits, pull_requests):
    """Return {member: stats} with a weighted score for each member."""
    stats = {}

    def entry(name):
        return stats.setdefault(
            name, {"commits": 0, "prs": 0, "merged_prs": 0, "reviews": 0, "score": 0}
        )

    for commit in commits:
        if is_meaningful_commit(commit["message"]):
            entry(commit["author"])["commits"] += 1

    for pr in pull_requests:
        author = entry(pr["author"])
        author["prs"] += 1
        if pr["merged"]:
            author["merged_prs"] += 1
        for review in pr["reviews"]:
            if review["reviewer"] != pr["author"]:
                entry(review["reviewer"])["reviews"] += 1

    for member in stats.values():
        member["score"] = (
            member["commits"] * WEIGHTS["commit"]
            + member["prs"] * WEIGHTS["pr_opened"]
            + member["merged_prs"] * WEIGHTS["pr_merged"]
            + member["reviews"] * WEIGHTS["review"]
        )
    return stats