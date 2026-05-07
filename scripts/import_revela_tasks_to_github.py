#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def gh_json(args: list[str], *, stdin: str | None = None) -> Any:
    cmd = ["gh", "api", *args]
    result = subprocess.run(
        cmd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown gh api error"
        raise RuntimeError(f"{' '.join(cmd)} failed: {message}")
    output = result.stdout.strip()
    return json.loads(output) if output else None


def ensure_gh_auth() -> None:
    result = run(["gh", "auth", "status"], check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "GitHub CLI is not authenticated. Run `gh auth login -h github.com -s repo,project` and rerun the importer."
        )


def infer_repo_from_git() -> str:
    result = run(["git", "config", "--get", "remote.origin.url"], check=False)
    if result.returncode != 0:
        raise RuntimeError("Could not read `remote.origin.url`; pass `--repo owner/name`.")
    remote = result.stdout.strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote)
    if not match:
        raise RuntimeError(f"Could not infer GitHub repo from remote URL: {remote}")
    return f"{match.group('owner')}/{match.group('repo')}"


def load_tasks(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        tasks = []
        for row in reader:
            labels = [label.strip() for label in row["labels"].split(",") if label.strip()]
            tasks.append(
                {
                    "title": row["title"].strip(),
                    "body": row["body"].strip(),
                    "labels": labels,
                    "milestone": row["milestone"].strip(),
                }
            )
    return tasks


def label_color(name: str) -> str:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    color = digest[:6]
    if int(color[:2], 16) < 64:
        color = f"7{color[1:]}"
    return color


def get_existing_labels(repo: str) -> dict[str, dict[str, Any]]:
    labels = gh_json([f"repos/{repo}/labels?per_page=100"])
    return {label["name"]: label for label in labels}


def canonical_label_map(existing: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {name.lower(): name for name in existing}


def ensure_labels(repo: str, tasks: list[dict[str, Any]], *, dry_run: bool) -> dict[str, dict[str, Any]]:
    existing = get_existing_labels(repo)
    existing_by_lower = canonical_label_map(existing)
    required = sorted({label for task in tasks for label in task["labels"]})
    for label in required:
        if label.lower() in existing_by_lower:
            continue
        if dry_run:
            print(f"[dry-run] would create label: {label}")
            existing[label] = {"name": label}
            existing_by_lower[label.lower()] = label
            continue
        created = gh_json(
            [
                "-X",
                "POST",
                f"repos/{repo}/labels",
                "-f",
                f"name={label}",
                "-f",
                f"color={label_color(label)}",
            ]
        )
        existing[label] = created
        existing_by_lower[label.lower()] = created["name"]
        print(f"created label: {label}")
    return existing


def get_existing_milestones(repo: str) -> dict[str, dict[str, Any]]:
    milestones = gh_json([f"repos/{repo}/milestones?state=all&per_page=100"])
    return {milestone["title"]: milestone for milestone in milestones}


def ensure_milestones(repo: str, tasks: list[dict[str, Any]], *, dry_run: bool) -> dict[str, dict[str, Any]]:
    existing = get_existing_milestones(repo)
    required = sorted({task["milestone"] for task in tasks if task["milestone"]})
    for title in required:
        if title in existing:
            continue
        if dry_run:
            print(f"[dry-run] would create milestone: {title}")
            existing[title] = {"title": title, "number": None}
            continue
        created = gh_json(
            [
                "-X",
                "POST",
                f"repos/{repo}/milestones",
                "-f",
                f"title={title}",
            ]
        )
        existing[title] = created
        print(f"created milestone: {title}")
    return existing


def get_existing_issues(repo: str) -> dict[str, dict[str, Any]]:
    issues = gh_json([f"repos/{repo}/issues?state=all&per_page=100"])
    filtered = [issue for issue in issues if "pull_request" not in issue]
    return {issue["title"]: issue for issue in filtered}


def get_project_v2_id(owner: str, project_title: str) -> str | None:
    user_query = """
    query($owner: String!, $search: String!) {
      user(login: $owner) {
        projectsV2(first: 100, query: $search) {
          nodes { id title }
        }
      }
    }
    """
    org_query = """
    query($owner: String!, $search: String!) {
      organization(login: $owner) {
        projectsV2(first: 100, query: $search) {
          nodes { id title }
        }
      }
    }
    """
    candidates: list[dict[str, str]] = []
    for gql in (user_query, org_query):
        result = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={gql}",
                "-F",
                f"owner={owner}",
                "-F",
                f"search={project_title}",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        data = json.loads(result.stdout.strip() or "{}")
        if data.get("data", {}).get("user"):
            candidates.extend(data["data"]["user"]["projectsV2"]["nodes"])
        if data.get("data", {}).get("organization"):
            candidates.extend(data["data"]["organization"]["projectsV2"]["nodes"])
    for project in candidates:
        if project["title"].strip().lower() == project_title.strip().lower():
            return project["id"]
    return None


def get_project_issue_ids(project_id: str) -> set[str]:
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              content {
                __typename
                ... on Issue {
                  id
                }
              }
            }
          }
        }
      }
    }
    """
    data = gh_json(
        [
            "graphql",
            "-f",
            f"query={query}",
            "-F",
            f"projectId={project_id}",
        ]
    )
    issue_ids: set[str] = set()
    items = data.get("data", {}).get("node", {}).get("items", {}).get("nodes", [])
    for item in items:
        content = item.get("content")
        if content and content.get("__typename") == "Issue":
            issue_ids.add(content["id"])
    return issue_ids


def add_issue_to_project(project_id: str, issue_node_id: str, *, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] would add issue node {issue_node_id} to project {project_id}")
        return
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={mutation}",
            "-F",
            f"projectId={project_id}",
            "-F",
            f"contentId={issue_node_id}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return
    stderr = result.stderr.strip()
    if "Content already exists in this project" in stderr:
        return
    raise RuntimeError(
        "gh api graphql addProjectV2ItemById failed: "
        f"{stderr or result.stdout.strip() or 'unknown error'}"
    )


def create_issue(
    repo: str,
    task: dict[str, Any],
    milestone_number: int | None,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        print(f"[dry-run] would create issue: {task['title']}")
        return {"number": None, "title": task["title"], "node_id": f"dry-run:{task['title']}"}

    args = [
        "-X",
        "POST",
        f"repos/{repo}/issues",
        "-f",
        f"title={task['title']}",
        "-f",
        f"body={task['body']}",
    ]
    for label in task["labels"]:
        args.extend(["-f", f"labels[]={label}"])
    if milestone_number is not None:
        args.extend(["-F", f"milestone={milestone_number}"])
    issue = gh_json(args)
    print(f"created issue #{issue['number']}: {issue['title']}")
    return issue


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import GitHub issues from revela_tasks.csv.")
    parser.add_argument("--csv", default="revela_tasks.csv", help="Path to the source CSV file.")
    parser.add_argument("--repo", help="Target repository in owner/name form. Defaults to origin remote.")
    parser.add_argument("--project-title", default="revela", help="GitHub Project v2 title to add issues to.")
    parser.add_argument("--project-owner", help="Owner that contains the GitHub project. Defaults to repo owner.")
    parser.add_argument(
        "--output",
        default="issue_import_results.json",
        help="Path for the import result log.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing to GitHub.")
    parser.add_argument(
        "--skip-project",
        action="store_true",
        help="Create issues without adding them to a GitHub project.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise RuntimeError(f"CSV file not found: {csv_path}")

    ensure_gh_auth()

    repo = args.repo or infer_repo_from_git()
    repo_owner = repo.split("/", 1)[0]
    project_owner = args.project_owner or repo_owner
    tasks = load_tasks(csv_path)

    print(f"loaded {len(tasks)} tasks from {csv_path}")
    labels = ensure_labels(repo, tasks, dry_run=args.dry_run)
    labels_by_lower = canonical_label_map(labels)
    for task in tasks:
        task["labels"] = [labels_by_lower.get(label.lower(), label) for label in task["labels"]]
    milestones = ensure_milestones(repo, tasks, dry_run=args.dry_run)
    existing_issues = get_existing_issues(repo)

    project_id: str | None = None
    project_issue_ids: set[str] = set()
    if not args.skip_project:
        project_id = get_project_v2_id(project_owner, args.project_title)
        if project_id is None:
            raise RuntimeError(
                f"Could not find GitHub Project v2 titled `{args.project_title}` under `{project_owner}`."
            )
        project_issue_ids = get_project_issue_ids(project_id)
        print(f"resolved project `{args.project_title}` under `{project_owner}`")

    results: list[dict[str, Any]] = []
    created_count = 0
    added_to_project_count = 0
    skipped_existing_count = 0

    for task in tasks:
        issue = existing_issues.get(task["title"])
        action = "existing"
        if issue is None:
            milestone = milestones.get(task["milestone"])
            milestone_number = None if milestone is None else milestone.get("number")
            issue = create_issue(repo, task, milestone_number, dry_run=args.dry_run)
            existing_issues[task["title"]] = issue
            created_count += 1
            action = "created"
        else:
            skipped_existing_count += 1

        added_to_project = False
        issue_node_id = issue.get("node_id")
        if project_id and issue_node_id and issue_node_id not in project_issue_ids:
            add_issue_to_project(project_id, issue_node_id, dry_run=args.dry_run)
            project_issue_ids.add(issue_node_id)
            added_to_project = True
            added_to_project_count += 1

        results.append(
            {
                "title": task["title"],
                "issue_number": issue.get("number"),
                "issue_node_id": issue.get("node_id"),
                "action": action,
                "added_to_project": added_to_project,
            }
        )

    write_results(Path(args.output), results)
    print(
        f"done: created {created_count}, reused {skipped_existing_count}, "
        f"added to project {added_to_project_count}, log written to {args.output}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
