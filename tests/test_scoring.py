from app.scoring import is_meaningful_commit, score_contributors


def test_merge_and_trivial_commits_are_ignored():
    assert not is_meaningful_commit("Merge branch 'main'")
    assert not is_meaningful_commit("fix")
    assert is_meaningful_commit("Add login page")


def test_scores_are_weighted():
    commits = [
        {"author": "alice", "message": "Add login page"},
        {"author": "alice", "message": "Merge branch 'main'"},
        {"author": "bob", "message": "fix"},
        {"author": "bob", "message": "Add database models"},
    ]
    pull_requests = [
        {
            "author": "alice",
            "merged": True,
            "reviews": [
                {"reviewer": "bob", "state": "APPROVED"},
                {"reviewer": "alice", "state": "COMMENTED"},
            ],
        }
    ]
    stats = score_contributors(commits, pull_requests)
    assert stats["alice"]["commits"] == 1
    assert stats["alice"]["score"] == 6
    assert stats["bob"]["score"] == 3