"""
Read, inspect and analyse Azure DevOps pipeline deployment logs.

Works with YAML pipelines (including deployment jobs) via the Azure DevOps
Build REST API. Optionally asks Claude to explain a failed run.

Setup:
  export AZDO_ORG=my-org
  export AZDO_PROJECT=my-project
  export AZDO_PAT=<personal access token with "Build (read)" scope>

Commands:
  python azdo_logs.py runs [--pipeline NAME] [--top 10] [--failed]
  python azdo_logs.py show RUN_ID            # stage/job/task tree with results
  python azdo_logs.py errors RUN_ID          # every ##[error] line + issues
  python azdo_logs.py logs RUN_ID [--out DIR] [--task NAME]
  python azdo_logs.py summarize RUN_ID       # Claude explains the failure

Add --demo to any command to use the bundled sample data (no credentials).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

API_VERSION = "7.1"
SAMPLE_DIR = Path(__file__).parent / "sample"
ERROR_PATTERNS = re.compile(
    r"##\[error\]|\berr(or)?\b|exception|failed|fatal|traceback|exit code [1-9]", re.IGNORECASE
)
TIMESTAMP_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s?")


# --------------------------------------------------------------------------- #
# API client
# --------------------------------------------------------------------------- #
class AzdoClient:
    """Thin wrapper over the Azure DevOps Build REST API."""

    def __init__(self, org: str, project: str, pat: str, host: str = "https://dev.azure.com"):
        self.base = f"{host}/{org}/{project}/_apis"
        token = base64.b64encode(f":{pat}".encode()).decode()
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Basic {token}"

    @classmethod
    def from_env(cls) -> "AzdoClient":
        missing = [k for k in ("AZDO_ORG", "AZDO_PROJECT", "AZDO_PAT") if not os.environ.get(k)]
        if missing:
            sys.exit(f"Missing environment variables: {', '.join(missing)} (or use --demo)")
        return cls(os.environ["AZDO_ORG"], os.environ["AZDO_PROJECT"], os.environ["AZDO_PAT"])

    def _get(self, path: str, params: dict | None = None, text: bool = False):
        params = {**(params or {}), "api-version": API_VERSION}
        headers = {"Accept": "text/plain"} if text else {"Accept": "application/json"}
        r = self.session.get(f"{self.base}/{path}", params=params, headers=headers, timeout=60)
        if r.status_code == 401:
            sys.exit("401 Unauthorized – check AZDO_PAT and that it has Build (read) scope.")
        if r.status_code == 203:
            sys.exit("Got an HTML sign-in page – the PAT is invalid or expired.")
        r.raise_for_status()
        return r.text if text else r.json()

    def list_builds(self, top: int = 10, definition: str | None = None, failed_only: bool = False) -> list[dict]:
        params: dict = {"$top": top, "queryOrder": "finishTimeDescending"}
        if definition:
            params["definitions"] = self._definition_id(definition)
        if failed_only:
            params["resultFilter"] = "failed"
        return self._get("build/builds", params)["value"]

    def _definition_id(self, name_or_id: str) -> int:
        if name_or_id.isdigit():
            return int(name_or_id)
        defs = self._get("build/definitions", {"name": name_or_id})["value"]
        if not defs:
            sys.exit(f"No pipeline named '{name_or_id}'")
        return defs[0]["id"]

    def get_build(self, build_id: int) -> dict:
        return self._get(f"build/builds/{build_id}")

    def get_timeline(self, build_id: int) -> list[dict]:
        return self._get(f"build/builds/{build_id}/timeline")["records"]

    def get_log(self, build_id: int, log_id: int) -> str:
        return self._get(f"build/builds/{build_id}/logs/{log_id}", text=True)


class DemoClient:
    """Serves the bundled sample data so the tool can be tried offline."""

    def list_builds(self, top=10, definition=None, failed_only=False):
        builds = json.loads((SAMPLE_DIR / "builds.json").read_text())["value"]
        if failed_only:
            builds = [b for b in builds if b.get("result") == "failed"]
        return builds[:top]

    def get_build(self, build_id):
        for b in self.list_builds(top=100):
            if b["id"] == build_id:
                return b
        sys.exit(f"Sample data has no run {build_id}. Try: python azdo_logs.py runs --demo")

    def get_timeline(self, build_id):
        return json.loads((SAMPLE_DIR / "timeline.json").read_text())["records"]

    def get_log(self, build_id, log_id):
        path = SAMPLE_DIR / f"log_{log_id}.txt"
        return path.read_text() if path.exists() else ""


# --------------------------------------------------------------------------- #
# Timeline model
# --------------------------------------------------------------------------- #
@dataclass
class Node:
    id: str
    name: str
    type: str          # Stage | Phase | Job | Task | Checkpoint
    result: str | None
    state: str
    start: str | None
    finish: str | None
    log_id: int | None
    issues: list[dict]
    children: list["Node"] = field(default_factory=list)

    @property
    def duration(self) -> str:
        if not (self.start and self.finish):
            return ""
        fmt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        secs = (fmt(self.finish) - fmt(self.start)).total_seconds()
        return f"{int(secs // 60)}m{int(secs % 60):02d}s" if secs >= 60 else f"{secs:.0f}s"

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def build_tree(records: list[dict]) -> list[Node]:
    nodes = {
        r["id"]: Node(
            id=r["id"],
            name=r.get("name", "?"),
            type=r.get("type", "?"),
            result=r.get("result"),
            state=r.get("state", "?"),
            start=r.get("startTime"),
            finish=r.get("finishTime"),
            log_id=(r.get("log") or {}).get("id"),
            issues=r.get("issues") or [],
        )
        for r in records
    }
    roots: list[Node] = []
    order = {r["id"]: r.get("order", 0) for r in records}
    for r in records:
        node = nodes[r["id"]]
        parent = nodes.get(r.get("parentId"))
        (parent.children if parent else roots).append(node)
    for n in nodes.values():
        n.children.sort(key=lambda c: order[c.id])
    roots.sort(key=lambda c: order[c.id])
    return roots


RESULT_ICON = {"succeeded": "✔", "failed": "✘", "canceled": "⊘", "skipped": "–",
               "succeededWithIssues": "⚠", None: "…"}


def print_tree(nodes: list[Node], depth: int = 0) -> None:
    for n in nodes:
        if n.type == "Checkpoint":
            continue
        icon = RESULT_ICON.get(n.result, "?")
        pad = "  " * depth
        print(f"{pad}{icon} [{n.type}] {n.name}  {n.duration}")
        for issue in n.issues:
            if issue.get("type") == "error":
                print(f"{pad}    ↳ {issue.get('message', '').strip()}")
        print_tree(n.children, depth + 1)


# --------------------------------------------------------------------------- #
# Log analysis
# --------------------------------------------------------------------------- #
def strip_timestamps(log: str) -> str:
    return "\n".join(TIMESTAMP_PREFIX.sub("", line) for line in log.splitlines())


def find_error_lines(log: str, context: int = 2) -> list[str]:
    """Return error lines with a little surrounding context."""
    lines = strip_timestamps(log).splitlines()
    keep: set[int] = set()
    for i, line in enumerate(lines):
        if ERROR_PATTERNS.search(line) and "##[warning]" not in line:
            keep.update(range(max(0, i - context), min(len(lines), i + context + 1)))
    out, prev = [], -2
    for i in sorted(keep):
        if i != prev + 1 and out:
            out.append("   ...")
        out.append(lines[i])
        prev = i
    return out


def failed_tasks(roots: list[Node]) -> list[Node]:
    return [n for r in roots for n in r.walk() if n.type == "Task" and n.result == "failed"]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_runs(client, args) -> None:
    builds = client.list_builds(top=args.top, definition=args.pipeline, failed_only=args.failed)
    if not builds:
        print("No runs found.")
        return
    print(f"{'ID':>8}  {'Result':<10} {'Pipeline':<30} {'Branch':<28} {'Finished':<20} By")
    for b in builds:
        finished = (b.get("finishTime") or "")[:19].replace("T", " ")
        branch = (b.get("sourceBranch") or "").replace("refs/heads/", "")
        who = (b.get("requestedFor") or {}).get("displayName", "")
        print(f"{b['id']:>8}  {b.get('result') or b.get('status'):<10} "
              f"{b['definition']['name'][:30]:<30} {branch[:28]:<28} {finished:<20} {who}")


def cmd_show(client, args) -> None:
    b = client.get_build(args.run_id)
    print(f"Run {b['id']} · {b['definition']['name']} · {b.get('result') or b.get('status')}")
    print(f"Branch: {b.get('sourceBranch')}  Commit: {(b.get('sourceVersion') or '')[:8]}")
    if url := (b.get("_links") or {}).get("web", {}).get("href"):
        print(f"URL: {url}")
    print()
    print_tree(build_tree(client.get_timeline(args.run_id)))


def cmd_errors(client, args) -> None:
    roots = build_tree(client.get_timeline(args.run_id))
    failed = failed_tasks(roots)
    if not failed:
        print("No failed tasks in this run.")
        return
    for task in failed:
        print(f"=== {task.name} (log {task.log_id}) ===")
        for issue in task.issues:
            print(f"issue: {issue.get('message', '').strip()}")
        if task.log_id:
            for line in find_error_lines(client.get_log(args.run_id, task.log_id)):
                print(line)
        print()


def cmd_logs(client, args) -> None:
    roots = build_tree(client.get_timeline(args.run_id))
    out = Path(args.out or f"run-{args.run_id}-logs")
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for n in (n for r in roots for n in r.walk()):
        if n.type != "Task" or not n.log_id:
            continue
        if args.task and args.task.lower() not in n.name.lower():
            continue
        safe = re.sub(r"[^\w.-]+", "_", n.name)[:60]
        path = out / f"{n.log_id:03d}_{safe}.log"
        path.write_text(client.get_log(args.run_id, n.log_id), encoding="utf-8")
        count += 1
    print(f"Wrote {count} log file(s) to {out}/")


def cmd_summarize(client, args) -> None:
    try:
        import anthropic
    except ImportError:
        sys.exit("pip install anthropic to use summarize")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY to use summarize")

    b = client.get_build(args.run_id)
    roots = build_tree(client.get_timeline(args.run_id))
    failed = failed_tasks(roots)
    if not failed:
        print("Run did not fail – nothing to summarise.")
        return

    sections = []
    for t in failed:
        excerpt = "\n".join(find_error_lines(client.get_log(args.run_id, t.log_id), context=8)) if t.log_id else ""
        issues = "\n".join(i.get("message", "") for i in t.issues)
        sections.append(f"### Task: {t.name}\nIssues:\n{issues}\n\nLog excerpt:\n{excerpt[-6000:]}")

    prompt = (
        f"An Azure DevOps pipeline run failed.\n"
        f"Pipeline: {b['definition']['name']}  Branch: {b.get('sourceBranch')}\n\n"
        + "\n\n".join(sections)
        + "\n\nIn plain language: (1) what failed, (2) the most likely root cause, "
          "(3) concrete next steps to fix it. Be brief."
    )
    resp = anthropic.Anthropic().messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    print("".join(blk.text for blk in resp.content if blk.type == "text"))


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Read Azure DevOps pipeline deployment logs")
    p.add_argument("--demo", action="store_true", help="use bundled sample data (no credentials)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("runs", help="list recent runs")
    s.add_argument("--pipeline", help="pipeline name or definition id")
    s.add_argument("--top", type=int, default=10)
    s.add_argument("--failed", action="store_true", help="only failed runs")
    s.set_defaults(fn=cmd_runs)

    for name, fn, hlp in (("show", cmd_show, "stage/job/task tree"),
                          ("errors", cmd_errors, "error lines from failed tasks"),
                          ("summarize", cmd_summarize, "ask Claude to explain a failure")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("run_id", type=int)
        s.set_defaults(fn=fn)

    s = sub.add_parser("logs", help="download task logs")
    s.add_argument("run_id", type=int)
    s.add_argument("--out", help="output directory")
    s.add_argument("--task", help="only tasks whose name contains this text")
    s.set_defaults(fn=cmd_logs)

    args = p.parse_args(argv)
    client = DemoClient() if args.demo else AzdoClient.from_env()
    args.fn(client, args)


if __name__ == "__main__":
    main()
