"""Task 4 (publish) — open one GitHub PR with the Genie Code revision proposals.

Reads   <catalog>.<schema>.revision_proposals (status='proposed', pr_url IS NULL) and .pages
Writes  revision_proposals.status -> pr_open | stale | blocked, pr_url

Safety:
  - stale:   the page on main no longer matches the body the proposal was based on
  - blocked: the proposed markdown contains workspace URLs, e-mail addresses or long numeric IDs
             (the site is public)
The PR is never merged here; a human reviews and merges.

Job usage (spark_python_task parameters):
  --catalog C --schema S --repo owner/name --secret-scope S --secret-key K
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import traceback
from datetime import UTC, datetime

import httpx
from pyspark.sql import SparkSession

API = "https://api.github.com"
SENSITIVE_RE = re.compile(
    r"cloud\.databricks\.com|azuredatabricks\.net|gcp\.databricks\.com"
    r"|[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+|\b\d{13,}\b"
)
JOB_RUN_NOTE_RE = re.compile(r"\s*\(job run [^)]*\)")


def gh(token: str) -> httpx.Client:
    return httpx.Client(
        base_url=API,
        timeout=30,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _json(r: httpx.Response) -> dict:
    if r.is_error:
        msg = r.json().get("message", "") if "json" in r.headers.get("content-type", "") else r.text[:200]
        raise RuntimeError(f"GitHub {r.request.method} {r.request.url.path} -> {r.status_code}: {msg}")
    return r.json()


def added_lines(base: str, new: str) -> str:
    """Lines present in the proposal but not in the base page — only these are screened."""
    old = set(base.splitlines())
    return "\n".join(ln for ln in new.splitlines() if ln not in old)


def file_on_main(c: httpx.Client, repo: str, path: str) -> str | None:
    r = c.get(f"/repos/{repo}/contents/{path}", params={"ref": "main"})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return base64.b64decode(r.json()["content"]).decode("utf-8")


def updates_rows(proposals: list, today: str) -> list[str]:
    rows = []
    for p in proposals:
        first = re.split(r"(?<=[.다])\s", JOB_RUN_NOTE_RE.sub("", p.rationale or "").strip())[0]
        first = first.replace("|", "\\|")[:200]
        src = " ".join(f"[원문]({u})" for u in (p.source_urls or [])[:3])
        rows.append(f"| {today} | {p.page_path.removeprefix('docs/')} | {first} | {src} |")
    return rows


def add_update_rows(updates_md: str, rows: list[str]) -> str:
    """Insert rows right under the changelog table header (newest first)."""
    sep = "|---|---|---|---|\n"
    if sep not in updates_md:
        return updates_md.rstrip("\n") + "\n" + "\n".join(rows) + "\n"
    return updates_md.replace(sep, sep + "\n".join(rows) + "\n", 1)


def pr_body(proposals: list) -> str:
    lines = [
        "Lakeflow Job `training-content-refresh`의 Genie Code 태스크가 공식 릴리즈 노트·블로그·인용 문서 변경을 읽고 만든 수정안입니다.",
        "**병합 전에 각 근거 원문을 확인해 주세요.** 수정안은 원문에 있는 사실만 반영하도록 지시되어 있습니다.",
        "",
    ]
    for p in proposals:
        lines.append(f"### `{p.page_path}` — {p.change_type}")
        lines.append(JOB_RUN_NOTE_RE.sub("", p.rationale or "").strip())
        for u in p.source_urls or []:
            lines.append(f"- {u}")
        lines.append("")
    return "\n".join(lines)


def check_token(c: httpx.Client, repo: str, token: str) -> None:
    """Fail early with a diagnosable message; never prints the token itself."""
    r = c.get(f"/repos/{repo}")
    if r.status_code == 401:
        raise RuntimeError(
            "GitHub rejected the token (401 Bad credentials): "
            f"length={len(token)}, github_pat_ prefix={token.startswith('github_pat_')}. "
            "Re-create the fine-grained PAT and store it again in the secret."
        )
    _json(r)
    # repo.permissions reflects the account, not the token — probe a harmless write instead
    # (an unreferenced blob is garbage-collected by GitHub).
    probe = c.post(f"/repos/{repo}/git/blobs", json={"content": "permission probe", "encoding": "utf-8"})
    if probe.status_code == 403:
        raise RuntimeError(
            "Token cannot write to the repo (403 on git/blobs): set Repository permissions -> "
            f"Contents: Read and write. GitHub says: {probe.json().get('message', '')}"
        )
    _json(probe)


def publish(spark: SparkSession, fq: str, repo: str, token: str, run_id: str) -> dict:
    proposals = spark.sql(f"""
        SELECT proposal_id, page_path, change_type, rationale, proposed_markdown, source_urls
        FROM {fq}.revision_proposals
        WHERE status = 'proposed' AND pr_url IS NULL AND proposed_markdown IS NOT NULL
        ORDER BY page_path, created_at""").collect()
    if not proposals:
        return {"proposed": 0}
    base_bodies = {r.path: r.body for r in spark.sql(f"SELECT path, body FROM {fq}.pages").collect()}

    ok, status = [], {}
    with gh(token) as c:
        check_token(c, repo, token)
        seen_paths = set()
        for p in proposals:
            repo_path = f"docs/{p.page_path}"
            if p.page_path in seen_paths:
                status[p.proposal_id] = "stale"  # a second proposal for the same page in one batch
                continue
            current = file_on_main(c, repo, repo_path)
            if current is None or current != base_bodies.get(p.page_path):
                status[p.proposal_id] = "stale"
                continue
            if SENSITIVE_RE.search(added_lines(current, p.proposed_markdown)):
                status[p.proposal_id] = "blocked"
                continue
            seen_paths.add(p.page_path)
            ok.append(p)

        if ok:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            branch = f"refresh/{today}-{run_id or datetime.now(UTC).strftime('%H%M%S')}"
            base_sha = _json(c.get(f"/repos/{repo}/git/ref/heads/main"))["object"]["sha"]
            base_tree = _json(c.get(f"/repos/{repo}/git/commits/{base_sha}"))["tree"]["sha"]
            updates_md = file_on_main(c, repo, "docs/updates.md") or "# 변경 이력\n"
            files = {f"docs/{p.page_path}": p.proposed_markdown for p in ok}
            files["docs/updates.md"] = add_update_rows(updates_md, updates_rows(ok, today))
            tree = [
                {"path": path, "mode": "100644", "type": "blob", "content": body}
                for path, body in files.items()
            ]
            tree_sha = _json(c.post(f"/repos/{repo}/git/trees", json={"base_tree": base_tree, "tree": tree}))[
                "sha"
            ]
            msg = f"Refresh {len(ok)} page(s) from release notes and docs changes ({today})"
            owner = repo.split("/", 1)[0]
            existing = _json(
                c.get(f"/repos/{repo}/pulls", params={"head": f"{owner}:{branch}", "state": "open"})
            )
            if existing:  # serverless retries re-run the task — reuse the PR opened by a previous attempt
                pr = existing[0]
                for p in ok:
                    status[p.proposal_id] = ("pr_open", pr["html_url"])
                return _finish(spark, fq, proposals, status, ok)
            commit = {"message": msg, "tree": tree_sha, "parents": [base_sha]}
            commit_sha = _json(c.post(f"/repos/{repo}/git/commits", json=commit))["sha"]
            ref = c.post(f"/repos/{repo}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": commit_sha})
            if ref.status_code == 422:  # branch left by a failed attempt — point it at the new commit
                _json(
                    c.patch(f"/repos/{repo}/git/refs/heads/{branch}", json={"sha": commit_sha, "force": True})
                )
            else:
                _json(ref)
            pr_req = {
                "title": f"[자동] 최신화 수정안 {len(ok)}건 ({today})",
                "head": branch,
                "base": "main",
                "body": pr_body(ok),
            }
            pr = _json(c.post(f"/repos/{repo}/pulls", json=pr_req))
            for p in ok:
                status[p.proposal_id] = ("pr_open", pr["html_url"])

    return _finish(spark, fq, proposals, status, ok)


def _finish(spark: SparkSession, fq: str, proposals: list, status: dict, ok: list) -> dict:
    rows = [(pid, v[0], v[1]) if isinstance(v, tuple) else (pid, v, None) for pid, v in status.items()]
    spark.createDataFrame(rows, "proposal_id STRING, st STRING, url STRING").createOrReplaceTempView("pub")
    spark.sql(f"""
        MERGE INTO {fq}.revision_proposals t USING pub s ON t.proposal_id = s.proposal_id
        WHEN MATCHED THEN UPDATE SET status = s.st, pr_url = s.url""")
    counts: dict = {"proposed": len(proposals)}
    for _, st, _u in rows:
        counts[st] = counts.get(st, 0) + 1
    if ok:
        counts["pr_url"] = status[ok[0].proposal_id][1]
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--secret-scope", required=True)
    ap.add_argument("--secret-key", required=True)
    ap.add_argument("--job-run-id", default="")
    args = ap.parse_args()

    from databricks.sdk.runtime import dbutils

    spark = SparkSession.builder.getOrCreate()
    fq = f"`{args.catalog}`.`{args.schema}`"
    started = datetime.now(UTC)
    stats: dict = {}
    error = None
    try:
        token = dbutils.secrets.get(
            scope=args.secret_scope, key=args.secret_key
        ).strip()  # pasted values may end in \n
        stats = publish(spark, fq, args.repo, token, args.job_run_id)
        print("publish", stats)
    except Exception:
        error = traceback.format_exc()[-4000:]
        raise
    finally:
        spark.createDataFrame(
            [(args.job_run_id, "publish", started, datetime.now(UTC), json.dumps(stats, default=str), error)],
            "job_run_id STRING, task STRING, started_at TIMESTAMP, finished_at TIMESTAMP, stats STRING, error STRING",
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.run_log")


if __name__ == "__main__":
    main()
