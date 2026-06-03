#!/usr/bin/env python3
"""
Collect recent GitHub activity for weekly reports.

This helper is intentionally conservative:
- org/owner defaults to the current repo's origin owner
- user defaults to the active gh login
- dates default to the last 7 calendar days
- GitHub search is enriched with local git history from sibling repos
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
from typing import Any


def run(
    cmd: list[str],
    *,
    cwd: pathlib.Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        message = stderr or stdout or f"command failed: {' '.join(cmd)}"
        raise RuntimeError(message)
    return result


def try_json(cmd: list[str], *, cwd: pathlib.Path | None = None) -> list[dict[str, Any]] | dict[str, Any] | None:
    try:
        result = run(cmd, cwd=cwd)
    except RuntimeError:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect GitHub weekly activity as JSON.")
    parser.add_argument("--org", help="GitHub owner/org to search. Defaults to current repo owner.")
    parser.add_argument("--login", help="GitHub login to search. Defaults to active gh login.")
    parser.add_argument("--current-repo", help="Current repo path. Defaults to cwd.")
    parser.add_argument(
        "--workspace",
        help="Workspace root containing sibling repos. Defaults to current repo parent.",
    )
    parser.add_argument("--start", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end", help="End date in YYYY-MM-DD format. Defaults to today (UTC).")
    parser.add_argument("--days", type=int, default=7, help="Calendar-day window when --start is omitted.")
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="Extra alias token or email to match in local git history. May be repeated.",
    )
    return parser.parse_args()


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def resolve_date_range(args: argparse.Namespace) -> tuple[dt.date, dt.date]:
    end = parse_date(args.end) if args.end else dt.datetime.now(dt.timezone.utc).date()
    if args.start:
        start = parse_date(args.start)
    else:
        start = end - dt.timedelta(days=max(args.days - 1, 0))
    if start > end:
        raise ValueError("start date must be on or before end date")
    return start, end


REMOTE_PATTERNS = [
    re.compile(r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$"),
    re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$"),
]


def parse_github_remote(url: str) -> tuple[str, str] | None:
    for pattern in REMOTE_PATTERNS:
        match = pattern.search(url.strip())
        if match:
            return match.group("owner"), match.group("repo")
    return None


def resolve_repo_path(args: argparse.Namespace) -> pathlib.Path:
    return pathlib.Path(args.current_repo or pathlib.Path.cwd()).resolve()


def resolve_owner(args: argparse.Namespace, repo_path: pathlib.Path) -> dict[str, Any]:
    if args.org:
        return {"owner": args.org, "repo": None, "source": "arg"}

    try:
        remote = run(["git", "remote", "get-url", "origin"], cwd=repo_path).stdout.strip()
    except RuntimeError:
        remote = ""
    parsed = parse_github_remote(remote) if remote else None
    if parsed:
        owner, repo = parsed
        return {"owner": owner, "repo": repo, "source": "git-remote", "remote": remote}

    data = try_json(["gh", "repo", "view", "--json", "owner,name"], cwd=repo_path)
    if isinstance(data, dict) and "owner" in data:
        owner = data["owner"]["login"]
        return {"owner": owner, "repo": data.get("name"), "source": "gh-repo-view"}

    raise RuntimeError("unable to resolve GitHub owner from the current repository")


def resolve_user(repo_path: pathlib.Path, login_override: str | None = None) -> dict[str, Any]:
    user: dict[str, Any] = {
        "login": login_override,
        "name": None,
        "email": None,
        "source": [],
    }
    if login_override:
        user["source"].append("arg-login")

    gh_user = try_json(["gh", "api", "user"], cwd=repo_path)
    if isinstance(gh_user, dict):
        user["login"] = gh_user.get("login")
        user["name"] = gh_user.get("name")
        user["source"].append("gh-api-user")

    auth_status = run(["gh", "auth", "status"], cwd=repo_path, check=False)
    auth_text = f"{auth_status.stdout}\n{auth_status.stderr}"
    match = re.search(r"account\s+([A-Za-z0-9_.-]+)\s+\(", auth_text)
    if match and not user["login"]:
        user["login"] = match.group(1)
    if match:
        user["source"].append("gh-auth-status")
    if auth_status.returncode != 0:
        user["source"].append("gh-auth-status-nonzero")

    try:
        git_name = run(["git", "config", "user.name"], cwd=repo_path).stdout.strip()
        if git_name:
            user.setdefault("git_name", git_name)
            user["source"].append("git-config-name")
    except RuntimeError:
        pass

    try:
        git_email = run(["git", "config", "user.email"], cwd=repo_path).stdout.strip()
        if git_email:
            user["email"] = git_email
            user["source"].append("git-config-email")
    except RuntimeError:
        pass

    return user


def build_alias_tokens(user: dict[str, Any], extra_aliases: list[str]) -> list[str]:
    tokens: set[str] = set()

    def add_token(value: str | None) -> None:
        if not value:
            return
        lowered = value.strip().lower()
        if not lowered:
            return
        tokens.add(lowered)
        for piece in re.split(r"[\s@._-]+", lowered):
            if len(piece) >= 3:
                tokens.add(piece)

    add_token(user.get("login"))
    add_token(user.get("name"))
    add_token(user.get("git_name"))
    add_token(user.get("email"))
    for alias in extra_aliases:
        add_token(alias)

    return sorted(tokens)


def build_exact_aliases(user: dict[str, Any], extra_aliases: list[str]) -> dict[str, set[str]]:
    names: set[str] = set()
    emails: set[str] = set()

    def add_name(value: str | None) -> None:
        if not value:
            return
        lowered = value.strip().lower()
        if lowered:
            names.add(lowered)

    def add_email(value: str | None) -> None:
        if not value:
            return
        lowered = value.strip().lower()
        if lowered:
            emails.add(lowered)

    add_name(user.get("login"))
    add_name(user.get("name"))
    add_name(user.get("git_name"))
    add_email(user.get("email"))

    for alias in extra_aliases:
        lowered = alias.strip().lower()
        if "@" in lowered:
            add_email(lowered)
        else:
            add_name(lowered)

    return {"names": names, "emails": emails}


def discover_local_repos(workspace_root: pathlib.Path, owner: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    seen: set[pathlib.Path] = set()
    candidates = [workspace_root]
    candidates.extend(
        child for child in workspace_root.iterdir() if child.is_dir() and child.name != ".git"
    )

    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if not (candidate / ".git").exists():
            continue
        try:
            remote = run(["git", "remote", "get-url", "origin"], cwd=candidate).stdout.strip()
        except RuntimeError:
            continue
        parsed = parse_github_remote(remote)
        if not parsed:
            continue
        repo_owner, repo_name = parsed
        if repo_owner != owner:
            continue
        repos.append(
            {
                "path": str(candidate),
                "owner": repo_owner,
                "repo": repo_name,
                "nameWithOwner": f"{repo_owner}/{repo_name}",
                "remote": remote,
            }
        )

    repos.sort(key=lambda item: item["nameWithOwner"])
    return repos


def gh_search_prs(owner: str, login: str, start: dt.date, mode: str) -> list[dict[str, Any]]:
    cmd = [
        "gh",
        "search",
        "prs",
        "--owner",
        owner,
        "--limit",
        "200",
        "--updated",
        f">={start.isoformat()}",
        "--json",
        "number,title,repository,author,state,createdAt,updatedAt,url",
    ]
    if mode == "author":
        cmd.extend(["--author", login])
    elif mode == "involves":
        cmd.extend(["--involves", login])
    else:
        raise ValueError(f"unknown PR search mode: {mode}")
    data = try_json(cmd)
    return data if isinstance(data, list) else []


def gh_enrich_pr(repo: str, number: int) -> dict[str, Any] | None:
    data = try_json(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            "number,title,state,author,createdAt,updatedAt,closedAt,mergedAt,mergedBy,headRefName,baseRefName,url",
        ]
    )
    return data if isinstance(data, dict) else None


def gh_search_issues(owner: str, login: str, start: dt.date, mode: str) -> list[dict[str, Any]]:
    cmd = [
        "gh",
        "search",
        "issues",
        "--owner",
        owner,
        "--limit",
        "200",
        "--updated",
        f">={start.isoformat()}",
        "--json",
        "number,title,repository,author,state,createdAt,updatedAt,closedAt,url",
    ]
    if mode == "author":
        cmd.extend(["--author", login])
    elif mode == "involves":
        cmd.extend(["--involves", login])
    else:
        raise ValueError(f"unknown issue search mode: {mode}")
    data = try_json(cmd)
    return data if isinstance(data, list) else []


def gh_search_commits(owner: str, login: str, start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    data = try_json(
        [
            "gh",
            "search",
            "commits",
            "--owner",
            owner,
            "--author",
            login,
            "--author-date",
            f">={start.isoformat()}",
            "--committer-date",
            f"<={(end + dt.timedelta(days=1)).isoformat()}",
            "--limit",
            "300",
            "--json",
            "sha,repository,commit,author,committer,url",
        ]
    )
    return data if isinstance(data, list) else []


def dedupe_records(items: list[dict[str, Any]], key_fn) -> list[dict[str, Any]]:
    seen: set[str] = set()
    ordered: list[dict[str, Any]] = []
    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def repo_default_remote_ref(repo_path: pathlib.Path) -> str:
    try:
        ref = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_path).stdout.strip()
        if ref:
            return ref.removeprefix("refs/remotes/")
    except RuntimeError:
        pass
    return "origin/main"


def matches_identity(name: str, email: str, exact_aliases: dict[str, set[str]]) -> bool:
    lowered_name = name.strip().lower()
    lowered_email = email.strip().lower()
    return lowered_name in exact_aliases["names"] or lowered_email in exact_aliases["emails"]


def collect_local_activity(
    repos: list[dict[str, Any]],
    start: dt.date,
    end: dt.date,
    exact_aliases: dict[str, set[str]],
) -> dict[str, Any]:
    local_commits: list[dict[str, Any]] = []
    mainline_merges: list[dict[str, Any]] = []
    raw_authors: set[str] = set()

    since = f"{start.isoformat()} 00:00:00"
    until = f"{(end + dt.timedelta(days=1)).isoformat()} 00:00:00"

    for repo in repos:
        repo_path = pathlib.Path(repo["path"])
        commit_log = run(
            [
                "git",
                "log",
                "--all",
                f"--since={since}",
                f"--until={until}",
                "--format=%H%x09%aI%x09%an%x09%ae%x09%s",
            ],
            cwd=repo_path,
            check=False,
        )
        for line in commit_log.stdout.splitlines():
            if not line.strip():
                continue
            sha, authored_at, author_name, author_email, subject = line.split("\t", 4)
            raw_authors.add(f"{author_name} <{author_email}>")
            if not matches_identity(author_name, author_email, exact_aliases):
                continue
            local_commits.append(
                {
                    "sha": sha,
                    "authoredAt": authored_at,
                    "authorName": author_name,
                    "authorEmail": author_email,
                    "subject": subject,
                    "repository": repo["nameWithOwner"],
                    "source": "local-git",
                }
            )

        merge_ref = repo_default_remote_ref(repo_path)
        merge_log = run(
            [
                "git",
                "log",
                merge_ref,
                "--first-parent",
                f"--since={since}",
                f"--until={until}",
                "--format=%H%x09%aI%x09%an%x09%ae%x09%cI%x09%cn%x09%ce%x09%s",
            ],
            cwd=repo_path,
            check=False,
        )
        for line in merge_log.stdout.splitlines():
            if not line.strip():
                continue
            (
                sha,
                authored_at,
                author_name,
                author_email,
                committed_at,
                committer_name,
                committer_email,
                subject,
            ) = line.split("\t", 7)
            if not (
                matches_identity(author_name, author_email, exact_aliases)
                or matches_identity(committer_name, committer_email, exact_aliases)
            ):
                continue
            if not (subject.startswith("Merge pull request #") or subject.startswith("Merge branch ")):
                continue
            pr_number = None
            match = re.search(r"#(\d+)", subject)
            if match:
                pr_number = int(match.group(1))
            mainline_merges.append(
                {
                    "sha": sha,
                    "authoredAt": authored_at,
                    "authorName": author_name,
                    "authorEmail": author_email,
                    "committedAt": committed_at,
                    "committerName": committer_name,
                    "committerEmail": committer_email,
                    "subject": subject,
                    "repository": repo["nameWithOwner"],
                    "prNumber": pr_number,
                    "source": "local-mainline",
                }
            )

    return {
        "reposScanned": repos,
        "rawAuthors": sorted(raw_authors),
        "commits": dedupe_records(local_commits, lambda item: item["sha"]),
        "mainlineMerges": dedupe_records(
            mainline_merges,
            lambda item: f"{item['repository']}#{item['sha']}",
        ),
    }


def authored_pr_key(item: dict[str, Any]) -> str:
    repo = item["repository"]["nameWithOwner"]
    return f"{repo}#{item['number']}"


def issue_key(item: dict[str, Any]) -> str:
    repo = item["repository"]["nameWithOwner"]
    return f"{repo}#{item['number']}"


def commit_key(item: dict[str, Any]) -> str:
    return item["sha"]


def main() -> int:
    args = parse_args()
    repo_path = resolve_repo_path(args)
    workspace_root = pathlib.Path(args.workspace).resolve() if args.workspace else repo_path.parent
    start, end = resolve_date_range(args)

    owner_info = resolve_owner(args, repo_path)
    user = resolve_user(repo_path, login_override=args.login)
    alias_tokens = build_alias_tokens(user, args.alias)
    exact_aliases = build_exact_aliases(user, args.alias)
    warnings: list[str] = []

    local_repos = discover_local_repos(workspace_root, owner_info["owner"])
    local = collect_local_activity(local_repos, start, end, exact_aliases)

    if not user.get("login"):
        warnings.append(
            "GitHub login could not be resolved from gh; GitHub API searches were skipped and only local git activity was collected."
        )
        authored_prs = []
        involved_prs = []
        authored_issues = []
        involved_issues = []
        gh_commits = []
    else:
        if "gh-auth-status-nonzero" in user.get("source", []):
            warnings.append(
                "gh auth status reported a non-zero result; login was inferred from the active account text and GitHub API results may be incomplete."
            )
        authored_prs = gh_search_prs(owner_info["owner"], user["login"], start, "author")
        involved_prs = gh_search_prs(owner_info["owner"], user["login"], start, "involves")
        authored_issues = gh_search_issues(owner_info["owner"], user["login"], start, "author")
        involved_issues = gh_search_issues(owner_info["owner"], user["login"], start, "involves")
        gh_commits = gh_search_commits(owner_info["owner"], user["login"], start, end)

    all_prs = dedupe_records(authored_prs + involved_prs, authored_pr_key)

    enriched_prs: list[dict[str, Any]] = []
    for pr in all_prs:
        repo_name = pr["repository"]["nameWithOwner"]
        enriched = gh_enrich_pr(repo_name, pr["number"])
        enriched_prs.append(enriched or pr)

    authored_pr_ids = {authored_pr_key(item) for item in authored_prs}
    for pr in enriched_prs:
        pr["relation"] = "author" if authored_pr_key(pr) in authored_pr_ids else "involves"

    enriched_issues = dedupe_records(authored_issues + involved_issues, issue_key)
    authored_issue_ids = {issue_key(item) for item in authored_issues}
    for issue in enriched_issues:
        issue["relation"] = "author" if issue_key(issue) in authored_issue_ids else "involves"

    normalized_gh_commits = []
    for item in gh_commits:
        normalized_gh_commits.append(
            {
                "sha": item["sha"],
                "authoredAt": item["commit"]["author"]["date"],
                "authorName": item["commit"]["author"]["name"],
                "authorEmail": item["commit"]["author"]["email"],
                "subject": item["commit"]["message"].splitlines()[0],
                "repository": item["repository"]["fullName"],
                "url": item["url"],
                "source": "gh-search",
            }
        )
    all_commits = dedupe_records(normalized_gh_commits + local["commits"], commit_key)

    authored_prs_enriched = [pr for pr in enriched_prs if pr.get("relation") == "author"]
    collaborative_merges = []
    authored_pr_lookup = {authored_pr_key(pr) for pr in authored_prs_enriched}
    for merge in local["mainlineMerges"]:
        pr_number = merge.get("prNumber")
        if pr_number is None:
            collaborative_merges.append(merge)
            continue
        key = f"{merge['repository']}#{pr_number}"
        if key not in authored_pr_lookup:
            collaborative_merges.append(merge)

    metrics = {
        "authored_prs": len(authored_prs_enriched),
        "merged_authored_prs": sum(1 for pr in authored_prs_enriched if pr.get("mergedAt")),
        "open_authored_prs": sum(1 for pr in authored_prs_enriched if str(pr.get("state", "")).upper() == "OPEN"),
        "collaborative_merges": len(collaborative_merges),
        "issues": len([issue for issue in enriched_issues if issue.get("relation") == "author"]),
        "open_issues": sum(
            1
            for issue in enriched_issues
            if issue.get("relation") == "author" and str(issue.get("state", "")).lower() == "open"
        ),
        "closed_issues": sum(
            1
            for issue in enriched_issues
            if issue.get("relation") == "author" and str(issue.get("state", "")).lower() != "open"
        ),
        "commits": len(all_commits),
        "repos_scanned": len(local_repos),
    }

    output = {
        "owner": owner_info,
        "user": user,
        "aliases": alias_tokens,
        "warnings": warnings,
        "dateRange": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": (end - start).days + 1,
        },
        "metrics": metrics,
        "gh": {
            "prs": enriched_prs,
            "issues": enriched_issues,
            "commits": normalized_gh_commits,
        },
        "local": {
            "reposScanned": local["reposScanned"],
            "rawAuthors": local["rawAuthors"],
            "commits": local["commits"],
            "mainlineMerges": local["mainlineMerges"],
            "collaborativeMerges": collaborative_merges,
        },
        "deduped": {
            "authoredPrs": authored_prs_enriched,
            "authoredIssues": [issue for issue in enriched_issues if issue.get("relation") == "author"],
            "commits": all_commits,
        },
    }

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
