from functools import lru_cache
from pathlib import Path

import requests
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.fairness import analyze_fairness
from app.github_client import get_commits, get_pull_requests, parse_repo_url
from app.scoring import is_meaningful_commit, score_contributors

app = FastAPI(title="Team Fairness Tracker")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@lru_cache(maxsize=32)
def fetch_and_score(owner, repo):
    commits = get_commits(owner, repo)
    pull_requests = get_pull_requests(owner, repo)
    stats = score_contributors(commits, pull_requests)
    return stats, commits


def group_commits(commits):
    """Group commits by author, marking which ones the scoring counts."""
    grouped = {}
    for commit in commits:
        first_line = commit["message"].strip().split("\n")[0]
        grouped.setdefault(commit["author"], []).append({
            "sha": commit["sha"][:7],
            "message": first_line,
            "date": commit["date"][:10],
            "counted": is_meaningful_commit(commit["message"]),
        })
    return grouped


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home(request: Request, repo_url: str = ""):
    context = {
        "repo_url": repo_url,
        "error": None,
        "result": None,
        "members": [],
        "commits_by_member": {},
        "chart_labels": [],
        "chart_values": [],
    }

    if repo_url:
        try:
            owner, repo = parse_repo_url(repo_url)
            stats, commits = fetch_and_score(owner, repo)
            members = sorted(
                stats.items(), key=lambda item: item[1]["score"], reverse=True
            )
            context["result"] = analyze_fairness(stats)
            context["members"] = members
            context["commits_by_member"] = group_commits(commits)
            context["chart_labels"] = [name for name, _ in members]
            context["chart_values"] = [data["score"] for _, data in members]
        except ValueError as error:
            context["error"] = str(error)
        except requests.HTTPError as error:
            status = error.response.status_code
            if status == 404:
                context["error"] = "Repository not found (it may be private)."
            elif status == 403:
                context["error"] = "GitHub rate limit reached. Try again later."
            else:
                context["error"] = f"GitHub returned an error ({status})."
        except requests.RequestException:
            context["error"] = "Could not reach GitHub. Check your internet connection."

    return templates.TemplateResponse(request, "index.html", context)