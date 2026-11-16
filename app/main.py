from pathlib import Path
from functools import lru_cache
import requests
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.fairness import analyze_fairness
from app.github_client import get_commits, get_pull_requests, parse_repo_url
from app.scoring import score_contributors

app = FastAPI(title="Team Fairness Tracker")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
@lru_cache(maxsize=32)
def fetch_and_score(owner, repo):
    commits = get_commits(owner, repo)
    pull_requests = get_pull_requests(owner, repo)
    return score_contributors(commits, pull_requests)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home(request: Request, repo_url: str = ""):
    context = {"repo_url": repo_url, "error": None, "result": None, "members": []}

    if repo_url:
        try:
            owner, repo = parse_repo_url(repo_url)
            stats = fetch_and_score(owner, repo)
            context["result"] = analyze_fairness(stats)
            context["members"] = sorted(
                stats.items(), key=lambda item: item[1]["score"], reverse=True
            )
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