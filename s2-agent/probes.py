from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any, Callable

ACCOUNT_ID = "29db7c74093386544fed8046ef083a4b"
CF_BASE = "https://api.cloudflare.com/client/v4"
WRANGLER = os.path.expanduser("~/cloudflare/tether/node_modules/.bin/wrangler")


def _cf_request(method: str, path: str, body: dict | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{CF_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {os.environ['CF_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _matches(actual: Any, expect: Any) -> bool:
    return actual == expect


def _d1_row(target: dict) -> bool:
    database_id = target["database_id"]
    table = _quote_identifier(target["table"])
    sql = f"SELECT * FROM {table} WHERE \"id\" = ?"
    payload = _cf_request(
        "POST",
        f"/accounts/{ACCOUNT_ID}/d1/database/{database_id}/query",
        {"sql": sql, "params": [target["id"]]},
    )
    if not payload.get("success"):
        return False
    results = payload.get("result") or []
    rows = results[0].get("results") or [] if results else []
    if len(rows) != 1:
        return False
    row = rows[0]
    return all(
        column in row and _matches(row[column], value)
        for column, value in target["expect"].items()
    )


def _kv_key(target: dict) -> bool:
    key = urllib.request.quote(str(target["key"]), safe="")
    req = urllib.request.Request(
        f"{CF_BASE}/accounts/{ACCOUNT_ID}/storage/kv/namespaces/"
        f"{target['namespace_id']}/values/{key}",
        headers={"Authorization": f"Bearer {os.environ['CF_TOKEN']}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode()
    except urllib.error.HTTPError:
        return False
    expect = target["expect"]
    if isinstance(expect, str):
        return text == expect
    try:
        return json.loads(text) == expect
    except ValueError:
        return False


def _r2_object(target: dict) -> bool:
    env = {**os.environ, "CLOUDFLARE_ACCOUNT_ID": ACCOUNT_ID}
    result = subprocess.run(
        [
            WRANGLER,
            "r2",
            "object",
            "get",
            f"{target['bucket']}/{target['key']}",
            "--remote",
            "--pipe",
        ],
        capture_output=True,
        env=env,
        timeout=120,
    )
    if result.returncode != 0:
        return False
    expect = target["expect"]
    try:
        body = result.stdout.decode()
    except UnicodeDecodeError:
        return False
    if isinstance(expect, str):
        return body == expect
    try:
        return json.loads(body) == expect
    except ValueError:
        return False


def _gh_json(args: list[str]) -> Any:
    result = subprocess.run(
        ["gh", "api", *args],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def _gh_pr(target: dict) -> bool:
    pr = _gh_json([f"repos/{target['repo']}/pulls/{target['number']}"])
    return target["expect"] == "merged" and pr.get("merged") is True


def _gh_actions(target: dict) -> bool:
    sha = target["sha"]
    result = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{target['repo']}/actions/runs?head_sha={sha}&per_page=100",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False
    pages = json.loads(result.stdout)
    runs = [run for page in pages for run in page.get("workflow_runs", [])]
    completed = [
        run
        for run in runs
        if run.get("head_sha") == sha and run.get("status") == "completed"
    ]
    return (
        target["expect"] == "success"
        and len(completed) > 0
        and all(run.get("conclusion") == "success" for run in completed)
    )


KINDS: dict[str, Callable[[dict], bool]] = {
    "d1_row": _d1_row,
    "kv_key": _kv_key,
    "r2_object": _r2_object,
    "gh_pr": _gh_pr,
    "gh_actions": _gh_actions,
}


def probe(kind: str, target: dict) -> bool:
    try:
        check = KINDS.get(kind)
        if check is None:
            return False
        return check(target) is True
    except Exception:
        return False
