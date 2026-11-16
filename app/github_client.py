from concurrent.futures import ThreadPoolExecutor
import os
import requests

API = "https://api.github.com"


def parse_repo_url(url):
    """Turn https://github.com/owner/repo into ("owner", "repo")."""
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("github.com/")
    if len(parts) != 2:
        raise ValueError("Not a valid GitHub URL")
    pieces = parts[1].split("/")
    if len(pieces) < 2:
        raise ValueError("URL must look like https://github.com/owner/repo")
    return pieces[0], pieces[1]


def _headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_commits(owner, repo, max_commits=100):
    """Fetch the latest commits of a repo."""
    url = f"{API}/repos/{owner}/{repo}/commits"
    response = requests.get(
        url, headers=_headers(), params={"per_page": max_commits}, timeout=15
    )
    response.raise_for_status()

    commits = []
    for item in response.json():
        author = item.get("author")
        commits.append({
            "sha": item["sha"],
            "author": author["login"] if author else item["commit"]["author"]["name"],
            "message": item["commit"]["message"],
            "date": item["commit"]["author"]["date"],
        })
    return commits

def get_reviews(owner, repo, pr_number):
    """Fetch the reviews given on one pull request."""
    url = f"{API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    response = requests.get(url, headers=_headers(), timeout=15)
    response.raise_for_status()

    reviews = []
    for item in response.json():
        user = item.get("user")
        if user:
            reviews.append({"reviewer": user["login"], "state": item["state"]})
    return reviews


def get_pull_requests(owner, repo, max_prs=20):
    """Fetch pull requests, each with its reviews (reviews fetched in parallel)."""
    url = f"{API}/repos/{owner}/{repo}/pulls"
    response = requests.get(
        url,
        headers=_headers(),
        params={"state": "all", "per_page": max_prs},
        timeout=15,
    )
    response.raise_for_status()

    def build(item):
        user = item.get("user")
        return {
            "number": item["number"],
            "author": user["login"] if user else "unknown",
            "title": item["title"],
            "merged": item["merged_at"] is not None,
            "reviews": get_reviews(owner, repo, item["number"]),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(build, response.json()))