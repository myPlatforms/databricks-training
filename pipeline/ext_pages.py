"""Ext tasks — keep standalone HTML pages (outside this repo) fresh.

One file, three job tasks (``--step``):
  collect  read each page in ext_pages.json from raw GitHub, snapshot the docs it cites,
           and queue (a) cited-doc changes and (b) release notes / blog items that mention
           the page's topics (read from source_items, filled by the training `collect` task)
  review   ai_query (structured output) per page with queued items -> literal edit list
           (find -> replace, each with an English evidence quote from the source)
  publish  apply edits that pass mechanical checks, open one PR per page in the page's repo;
           anything left for a human (needs_research, dropped edits) goes to a GitHub issue

Tables (in <catalog>.<schema>, separate from the training tables): ext_pages,
ext_doc_snapshots, ext_queue, ext_proposals. run_log is shared (task = ext_<step>).

Why edits instead of a rewritten page: the pages are hand-built HTML with inline SVG and
scripts (~75 KB). Regenerating the whole file invites silent damage, so the model may only
replace short literal strings that occur exactly once, outside <svg>/<script>/<style>.

Local self-test (no Spark):  uv run --frozen --with httpx python pipeline/ext_pages.py --selftest
"""

from __future__ import annotations

import argparse
import html as htmllib
import json
import os
import re
import sys
import traceback
import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

# Serverless spark_python_task runs the file via exec() without __file__; argv[0] is the path.
_here = (
    globals().get("__file__")
    or globals().get("filename")  # set by the serverless exec() wrapper
    or (sys.argv[0] if sys.argv and sys.argv[0].endswith(".py") else "")
)
sys.path.insert(0, os.path.dirname(os.path.abspath(_here)) if _here else os.getcwd())

import sources

SITE_TZ = ZoneInfo("Asia/Seoul")
BASIS_RE = re.compile(r"(기준일\s*:?\s*)(\d{4}-\d{2}-\d{2})")
HREF_RE = re.compile(r'href="(https?://[^"#\s]+)')
PROTECTED_RE = re.compile(r"(?is)<(svg|script|style)\b.*?</\1\s*>")
MAIN_RE = re.compile(r"(?is)<main\b.*?</main\s*>")
# Same screen as publish.py: the pages are public.
SENSITIVE_RE = re.compile(
    r"cloud\.databricks\.com|azuredatabricks\.net|gcp\.databricks\.com"
    r"|[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+|\b\d{13,}\b"
)
STRUCTURE_TAGS = ("section", "svg", "script", "style", "figure", "table", "nav", "main", "h2", "h3")
ITEM_BODY_MAX = 5000
FIND_MAX = 600

DECISIONS = ["edit", "no_change", "needs_research"]
RESPONSE_FORMAT = json.dumps(
    {
        "type": "json_schema",
        "json_schema": {
            "name": "ext_page_edits",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string", "enum": DECISIONS},
                    "rationale_ko": {"type": "string"},
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "find": {"type": "string"},
                                "replace": {"type": "string"},
                                "evidence_quote": {"type": "string"},
                                "item_id": {"type": "string"},
                                "source_url": {"type": "string"},
                                "why_ko": {"type": "string"},
                            },
                            "required": [
                                "find",
                                "replace",
                                "evidence_quote",
                                "item_id",
                                "source_url",
                                "why_ko",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "research_notes_ko": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["decision", "rationale_ko", "edits", "research_notes_ko"],
                "additionalProperties": False,
            },
        },
    }
)

INSTRUCTIONS = """\
당신은 공개 한국어 안내 페이지 {site} 의 편집자입니다. 페이지는 Databricks 공식 문서만 근거로 씁니다.
아래 '변경 항목'(릴리스 노트, 블로그, 또는 페이지가 인용한 공식 문서의 변경 diff)이 이 페이지가 설명하는 사실
(기능, 상태 라벨, 이름, 날짜, 한도, 권한, 절차, 링크)을 바꾸거나 보강하는지 판정하고, 필요하면 최소한의 수정 목록을 만듭니다.

판정
- decision="no_change": 항목이 페이지의 사실을 바꾸지 않음(이미 반영됨, 범위 밖, 마케팅성 글, 서식만 바뀐 diff).
- decision="edit": 바꿀 사실이 있고, 근거 문장이 항목 원문에 있음.
- decision="needs_research": 관련은 있지만 원문만으로 정확한 문장을 쓸 수 없음 → research_notes_ko에 무엇을 확인해야 하는지 적음.

수정(edits) 규칙 — 반드시 지킬 것
- find: 아래 '페이지 HTML'에 있는 문자열을 태그까지 **한 글자도 바꾸지 않고** 그대로 복사합니다. 짧게(한 문장, 표 한 칸, 목록 한 줄 정도) 잡되,
  페이지 전체에서 **정확히 한 번만** 나오도록 충분히 길게 잡습니다. <svg>, <script>, <style> 안은 고치지 않습니다(페이지 HTML에서 생략돼 있음).
- replace: find를 대신할 HTML. 바뀌는 사실만 고치고 나머지 글자·태그·class는 그대로 둡니다. 합니다체, 제품명과 상태 라벨(GA, Public Preview, Beta)은 원문 표기 그대로.
- evidence_quote: 바꾼 사실의 근거가 되는 **영어 원문 문장 그대로**(항목 body에서 복사, diff면 '+'로 시작하는 줄의 내용). 원문에 없는 사실은 쓰지 않습니다.
- item_id / source_url: 근거 항목의 item_id와 url.
- why_ko: 무엇을 왜 바꾸는지 한국어 한 문장.
- 기준일(“기준일 YYYY-MM-DD”)은 고치지 않습니다. 발행 단계에서 일괄 갱신합니다.
- 새 기능을 소개하는 문장을 추가해야 하면, 관련 목록·표의 기존 한 줄을 find로 잡고 replace에 그 줄 + 새 줄을 씁니다.
- 상태표(#status)의 행을 바꾸거나 추가할 수 있습니다. 참고 문서 목록에 근거 URL이 없으면 같은 형식으로 추가합니다.
- 고객사명, 사내 링크, 워크스페이스 URL·ID, 이메일은 절대 쓰지 않습니다.

rationale_ko: 판정 근거를 한국어 2~3문장으로.

## 변경 항목 (item_id | source | date | url | title, 그리고 body)
{items}

## 페이지 HTML (<main> 부분, svg·script·style 생략)
{page}
"""


# ---- Pure helpers (locally testable) ----


def load_config(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        cfgs = json.load(f)
    for c in cfgs:
        for k in ("key", "repo", "branch", "path", "site", "topics"):
            if k not in c:
                raise ValueError(f"ext page config {c.get('key')!r} misses {k!r}")
    return cfgs


def raw_url(cfg: dict) -> str:
    return f"https://raw.githubusercontent.com/{cfg['repo']}/{cfg['branch']}/{cfg['path']}"


def _is_docs_leaf(url: str) -> bool:
    path = url.split("://", 1)[-1].split("#", 1)[0].rstrip("/")
    return path.count("/") >= 3


def cited_doc_urls(raw: str) -> list[str]:
    """Docs pages the page links to. Release-notes pages are left to the RSS feed (they change daily)."""
    out = []
    for u in HREF_RE.findall(htmllib.unescape(raw)):
        u = u.split("?", 1)[0]
        is_docs = "docs.databricks.com" in u or "learn.microsoft.com" in u
        if is_docs and _is_docs_leaf(u) and "/release-notes/" not in u:
            out.append(u)
    return list(dict.fromkeys(out))


def page_record(cfg: dict, raw: str) -> dict:
    m = BASIS_RE.search(raw)
    main = MAIN_RE.search(raw)
    return {
        "page_key": cfg["key"],
        "repo": cfg["repo"],
        "path": cfg["path"],
        "basis_date": date.fromisoformat(m.group(2)) if m else None,
        "body": raw,
        "text": sources.html_to_text(main.group(0) if main else raw),
        "content_hash": sources.sha1(raw),
        "cited_urls": cited_doc_urls(raw),
    }


def review_html(raw: str) -> str:
    """The <main> HTML the model sees: protected blocks collapsed so it cannot target them."""
    main = MAIN_RE.search(raw)
    body = main.group(0) if main else raw
    return PROTECTED_RE.sub(lambda m: f"<{m.group(1)}>…(생략)…</{m.group(1)}>", body)


def protected_spans(raw: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in PROTECTED_RE.finditer(raw)]


def _norm(s: str) -> str:
    s = htmllib.unescape(s)
    s = re.sub(r"[‘’]", "'", re.sub(r"[“”]", '"', s))
    return re.sub(r"\s+", " ", s).strip().lower()


def structure(raw: str) -> dict:
    counts = {t: len(re.findall(rf"(?i)<{t}\b", raw)) for t in STRUCTURE_TAGS}
    counts["scripts"] = [sources.sha1(m.group(0)) for m in re.finditer(r"(?is)<script\b.*?</script\s*>", raw)]
    counts["ids"] = sorted(re.findall(r'\bid="([^"]+)"', raw))
    return counts


def apply_edits(raw: str, edits: list[dict], item_bodies: dict[str, str]) -> tuple[str, list, list]:
    """Apply edits that pass every check; return (new_html, applied, dropped[(edit, reason)])."""
    new, applied, dropped = raw, [], []
    all_bodies = "\n".join(item_bodies.values())
    for e in edits:
        find, rep = e.get("find") or "", e.get("replace") or ""
        reason = None
        if not find or find == rep:
            reason = "find가 비었거나 replace와 같음"
        elif len(find) > FIND_MAX:
            reason = f"find가 너무 김({len(find)}자)"
        elif (n := new.count(find)) != 1:
            reason = f"find가 현재 페이지에 {n}번 나옴(정확히 1번이어야 함)"
        elif any(s <= new.index(find) < t for s, t in protected_spans(new)):
            reason = "svg·script·style 안을 고치려 함"
        elif BASIS_RE.search(find) or BASIS_RE.search(rep):
            reason = "기준일은 발행 단계에서만 바꿈"
        elif SENSITIVE_RE.search(rep):
            reason = "replace에 워크스페이스 URL·이메일·긴 숫자 ID가 있음"
        else:
            quote = _norm(e.get("evidence_quote") or "").lstrip("+ ").strip()
            body = item_bodies.get(e.get("item_id") or "") or all_bodies
            if len(quote) < 12 or quote not in _norm(body):
                reason = "근거 인용이 항목 원문에 없음"
        if reason:
            dropped.append((e, reason))
            continue
        candidate = new.replace(find, rep, 1)
        if structure(candidate) != structure(new):
            dropped.append((e, "페이지 구조(섹션·그림·표·스크립트·id)가 바뀜"))
            continue
        new = candidate
        applied.append(e)
    return new, applied, dropped


def bump_basis(raw: str, today: str) -> str:
    return BASIS_RE.sub(rf"\g<1>{today}", raw)


def plain(s: str, n: int = 240) -> str:
    t = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
    return t if len(t) <= n else t[:n] + "…"


def build_prompt(cfg: dict, raw: str, items: list[dict]) -> str:
    blocks = []
    for it in items:
        body = (it.get("body") or "")[:ITEM_BODY_MAX]
        blocks.append(
            f"### {it['item_id']} | {it['source']} | {it.get('published_date')} | {it['url']} | {it.get('title', '')}\n"
            f"{body}"
        )
    return INSTRUCTIONS.format(site=cfg["site"], items="\n\n".join(blocks), page=review_html(raw))


# ---- Spark steps ----

PAGE_DDL = (
    "page_key STRING, repo STRING, path STRING, basis_date DATE, body STRING, text STRING, "
    "content_hash STRING, cited_urls ARRAY<STRING>"
)
QUEUE_DDL = (
    "page_key STRING, item_id STRING, source STRING, url STRING, title STRING, "
    "published_date DATE, body STRING"
)


def ensure_tables(spark, fq: str) -> None:
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.ext_pages ({PAGE_DDL}, fetched_at TIMESTAMP)
        COMMENT 'Ext refresh: current standalone pages (raw HTML) from ext_pages.json'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.ext_doc_snapshots (
          page_key STRING, url STRING, title STRING, last_updated DATE, content_hash STRING,
          body STRING, fetched_at TIMESTAMP)
        COMMENT 'Ext refresh: snapshot history of docs cited by standalone pages'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.ext_queue ({QUEUE_DDL},
          status STRING COMMENT 'queued | reviewed', proposal_id STRING,
          queued_at TIMESTAMP, reviewed_at TIMESTAMP)
        COMMENT 'Ext refresh: items waiting for review, per page'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.ext_proposals (
          proposal_id STRING NOT NULL, page_key STRING, item_ids ARRAY<STRING>,
          decision STRING, rationale STRING, edits STRING, research_notes ARRAY<STRING>,
          source_urls ARRAY<STRING>, base_hash STRING, model STRING, job_run_id STRING,
          status STRING COMMENT 'proposed | rejected | needs_research | pr_open | issue_open | stale | dropped | error',
          pr_url STRING, issue_url STRING, report STRING, created_at TIMESTAMP)
        COMMENT 'Ext refresh: literal edit proposals per page (ai_query) and their publish outcome'""")


def topic_regex(topics: list[str]) -> str:
    return "|".join(re.escape(t.lower()) for t in topics)


def step_collect(spark, fq: str, cfgs: list[dict]) -> dict:
    stats: dict = {}
    pages = []
    with sources.http_client() as client:
        for cfg in cfgs:
            r = client.get(raw_url(cfg))
            r.raise_for_status()
            pages.append((cfg, page_record(cfg, r.text)))
        rows = [{k: v for k, v in p.items()} for _, p in pages]
        spark.createDataFrame(rows, PAGE_DDL).createOrReplaceTempView("ext_incoming_pages")
        spark.sql(f"""
            INSERT OVERWRITE {fq}.ext_pages
            SELECT page_key, repo, path, basis_date, body, text, content_hash, cited_urls, current_timestamp()
            FROM ext_incoming_pages""")

        prev = {
            (r.page_key, r.url): r
            for r in spark.sql(f"""
                SELECT page_key, url, last_updated, content_hash, body FROM (
                  SELECT *, row_number() OVER (PARTITION BY page_key, url ORDER BY fetched_at DESC) rn
                  FROM {fq}.ext_doc_snapshots) WHERE rn = 1""").collect()
        }
        snaps, queue = [], []
        for cfg, p in pages:
            st = {
                "cited": len(p["cited_urls"]),
                "errors": 0,
                "doc_change": 0,
                "basis_date": str(p["basis_date"]),
            }
            for url in p["cited_urls"]:
                try:
                    s = sources.fetch_doc_snapshot(client, url)
                except Exception as e:  # noqa: BLE001 — one bad page must not fail the run
                    st["errors"] += 1
                    print(f"doc fetch failed {url}: {e}")
                    continue
                snaps.append(
                    {"page_key": cfg["key"]}
                    | {k: s[k] for k in ("url", "title", "last_updated", "content_hash", "body")}
                )
                old = prev.get((cfg["key"], url))
                if old is None:
                    continue  # first snapshot = baseline
                date_changed = s["last_updated"] is not None and s["last_updated"] != old.last_updated
                text_changed = s["last_updated"] is None and s["content_hash"] != old.content_hash
                if not (date_changed or text_changed):
                    continue
                diff = sources.text_diff(old.body or "", s["body"])
                if not diff.strip():
                    continue
                queue.append(
                    {
                        "page_key": cfg["key"],
                        "item_id": sources.sha1(
                            f"{cfg['key']}|{url}|{s['last_updated']}|{s['content_hash']}"
                        ),
                        "source": "doc_change",
                        "url": url,
                        "title": s["title"],
                        "published_date": s["last_updated"] or date.today(),
                        "body": diff,
                    }
                )
                st["doc_change"] += 1
            stats[cfg["key"]] = st
    if snaps:
        spark.createDataFrame(
            snaps,
            "page_key STRING, url STRING, title STRING, last_updated DATE, content_hash STRING, body STRING",
        ).createOrReplaceTempView("ext_incoming_snaps")
        spark.sql(f"""
            INSERT INTO {fq}.ext_doc_snapshots
            SELECT page_key, url, title, last_updated, content_hash, body, current_timestamp() FROM ext_incoming_snaps""")

    # Release notes and blog posts collected by the training `collect` task, filtered by topic.
    for cfg, p in pages:
        if p["basis_date"] is None:
            raise RuntimeError(f"{cfg['key']}: no '기준일 YYYY-MM-DD' found in the page")
        hits = spark.sql(
            f"""SELECT :k AS page_key, item_id, source, url, title, published_date, body
                FROM {fq}.source_items
                WHERE source IN ('release_notes', 'blog') AND status <> 'baseline'
                  AND published_date >= :basis
                  AND (lower(title) RLIKE :pat OR lower(body) RLIKE :pat)""",
            args={"k": cfg["key"], "basis": p["basis_date"], "pat": topic_regex(cfg["topics"])},
        ).collect()
        queue += [h.asDict() for h in hits]
        stats[cfg["key"]]["topic_items"] = len(hits)

    if queue:
        spark.createDataFrame(queue, QUEUE_DDL).createOrReplaceTempView("ext_incoming_queue")
        spark.sql(f"""
            MERGE INTO {fq}.ext_queue t
            USING (SELECT * FROM ext_incoming_queue) s
            ON t.page_key = s.page_key AND t.item_id = s.item_id
            WHEN NOT MATCHED THEN INSERT (page_key, item_id, source, url, title, published_date, body,
              status, proposal_id, queued_at, reviewed_at)
              VALUES (s.page_key, s.item_id, s.source, s.url, s.title, s.published_date, s.body,
              'queued', NULL, current_timestamp(), NULL)""")
    stats["pending"] = spark.sql(f"SELECT count(*) c FROM {fq}.ext_queue WHERE status = 'queued'").first().c
    return stats


def step_review(spark, fq: str, cfgs: list[dict], endpoint: str, run_id: str, max_items: int) -> dict:
    pages = {
        r.page_key: r for r in spark.sql(f"SELECT page_key, body, content_hash FROM {fq}.ext_pages").collect()
    }
    prompts, included = [], {}
    for cfg in cfgs:
        page = pages.get(cfg["key"])
        if page is None:
            continue
        items = [
            r.asDict()
            for r in spark.sql(
                f"""SELECT item_id, source, url, title, published_date, body FROM {fq}.ext_queue
                    WHERE page_key = :k AND status = 'queued'
                    ORDER BY published_date, item_id LIMIT {int(max_items)}""",
                args={"k": cfg["key"]},
            ).collect()
        ]
        if items:
            prompts.append((cfg["key"], build_prompt(cfg, page.body, items)))
            included[cfg["key"]] = items
    if not prompts:
        return {"pages": 0}

    fmt = RESPONSE_FORMAT.replace("'", "\\'")
    spark.createDataFrame(prompts, "page_key STRING, prompt STRING").createOrReplaceTempView("ext_prompts")
    # Materialize once so ai_query is not re-evaluated by later statements.
    spark.sql(f"""
        SELECT page_key, r.result AS result, r.errorMessage AS error FROM (
          SELECT page_key, ai_query('{endpoint}', prompt, responseFormat => '{fmt}', failOnError => false) AS r
          FROM ext_prompts)""").write.mode("overwrite").saveAsTable(f"{fq}._ext_review_tmp")
    results = spark.sql(f"SELECT page_key, result, error FROM {fq}._ext_review_tmp").collect()
    spark.sql(f"DROP TABLE IF EXISTS {fq}._ext_review_tmp")

    rows, stats = [], {"pages": len(prompts)}
    for r in results:
        items = included[r.page_key]
        pid = str(uuid.uuid4())
        try:
            if r.error:
                raise ValueError(r.error)
            j = json.loads(r.result)
            decision = j["decision"]
            edits = j["edits"] if decision == "edit" else []
            status = {"edit": "proposed", "no_change": "rejected", "needs_research": "needs_research"}[
                decision
            ]
            if decision == "edit" and not edits:
                status = "rejected"
            rationale, notes = j.get("rationale_ko", ""), j.get("research_notes_ko", [])
        except Exception as e:  # noqa: BLE001 — record and keep the items queued for the next run
            print(f"review failed for {r.page_key}: {e}")
            decision, edits, status, rationale, notes = "error", [], "error", str(e)[:2000], []
        urls = sorted(
            {e.get("source_url") for e in edits if e.get("source_url")} or {i["url"] for i in items}
        )
        rows.append(
            (
                pid,
                r.page_key,
                [i["item_id"] for i in items],
                decision,
                rationale,
                json.dumps(edits, ensure_ascii=False),
                notes,
                urls,
                pages[r.page_key].content_hash,
                endpoint,
                run_id,
                status,
            )
        )
        stats[r.page_key] = {"decision": decision, "edits": len(edits), "items": len(items)}
        if status != "error":
            spark.createDataFrame(
                [(r.page_key, i["item_id"]) for i in items], "page_key STRING, item_id STRING"
            ).createOrReplaceTempView("ext_done")
            spark.sql(f"""
                MERGE INTO {fq}.ext_queue t USING ext_done s
                ON t.page_key = s.page_key AND t.item_id = s.item_id
                WHEN MATCHED THEN UPDATE SET status = 'reviewed', proposal_id = '{pid}',
                  reviewed_at = current_timestamp()""")
    spark.createDataFrame(
        rows,
        "proposal_id STRING, page_key STRING, item_ids ARRAY<STRING>, decision STRING, rationale STRING, "
        "edits STRING, research_notes ARRAY<STRING>, source_urls ARRAY<STRING>, base_hash STRING, "
        "model STRING, job_run_id STRING, status STRING",
    ).createOrReplaceTempView("ext_new_props")
    spark.sql(f"""
        INSERT INTO {fq}.ext_proposals
        SELECT proposal_id, page_key, item_ids, decision, rationale, edits, research_notes, source_urls,
               base_hash, model, job_run_id, status, NULL, NULL, NULL, current_timestamp()
        FROM ext_new_props""")
    if all(row[-1] == "error" for row in rows):
        raise RuntimeError(f"all {len(rows)} ext reviews failed: {rows[0][4][:300]}")
    return stats


def svg_followups(raw: str, applied: list) -> list[str]:
    """SVG text the edits cannot touch but that still carries a word the edits removed."""
    removed = set()
    for e in applied:
        before, after = (
            set(re.findall(r"[\w가-힣.-]{2,}", plain(e["find"], 10**6))),
            plain(e["replace"], 10**6),
        )
        removed |= {w for w in before if w not in after}
    texts = [
        plain(m.group(1), 200)
        for svg in re.finditer(r"(?is)<svg\b.*?</svg\s*>", raw)
        for m in re.finditer(r"(?is)<text\b[^>]*>(.*?)</text>", svg.group(0))
    ]
    return sorted({t for t in texts if any(w in t for w in removed)})


def pr_body(cfg: dict, applied: list, dropped: list, props: list, followups: list[str] | None = None) -> str:
    lines = [
        f"Lakeflow Job `training-content-refresh`의 ext 태스크가 공식 릴리스 노트·블로그·인용 문서 변경을 읽고 만든 **{cfg['key']}** 페이지 수정안입니다.",
        "각 수정은 원문 근거 문장이 항목 원문에 실제로 있는지, 고치는 문자열이 페이지에 정확히 한 번 있는지, 페이지 구조가 그대로인지를 코드로 확인했습니다.",
        "**병합 전에 근거 원문을 확인해 주세요.** 기준일은 이 실행 날짜로 바꿨습니다.",
        "",
        "## 적용한 수정",
    ]
    for e in applied:
        lines += [
            f"- {e.get('why_ko', '')}",
            f"  - 전: {plain(e['find'])}",
            f"  - 후: {plain(e['replace'])}",
            f'  - 근거: "{e.get("evidence_quote", "")[:300]}" — {e.get("source_url", "")}',
        ]
    if dropped:
        lines += ["", "## 적용하지 않은 수정 (검토 필요)"]
        for e, why in dropped:
            lines.append(
                f"- {why}: {plain(e.get('find', ''), 120)} → {plain(e.get('replace', ''), 120)} ({e.get('source_url', '')})"
            )
    if followups:
        lines += [
            "",
            "## 그림(SVG) 안 확인 필요",
            "자동 수정은 그림 안 글자를 고치지 않습니다. 아래 글자가 위 수정과 맞는지 직접 확인해 주세요.",
        ]
        lines += [f"- {t}" for t in followups]
    lines += ["", "## 판정 근거"]
    for p in props:
        lines.append(f"- {p.rationale}")
    return "\n".join(lines)


def issue_body(cfg: dict, notes: list[str], dropped: list, props: list) -> str:
    lines = [f"ext 태스크가 **{cfg['key']}** 페이지에서 사람이 확인해야 할 항목을 찾았습니다.", ""]
    for n in notes:
        lines.append(f"- {n}")
    for e, why in dropped:
        lines.append(
            f"- 적용 못 한 수정({why}): {plain(e.get('replace', ''), 160)} — {e.get('source_url', '')}"
        )
    lines += ["", "근거 URL:"]
    for p in props:
        for u in p.source_urls or []:
            lines.append(f"- {u}")
    return "\n".join(lines)


def step_publish(spark, fq: str, cfgs: list[dict], token: str, run_id: str) -> dict:
    import publish as pub  # GitHub helpers (gh, _json, file_on_main, check_token)

    today = datetime.now(SITE_TZ).strftime("%Y-%m-%d")
    stats: dict = {}
    updates = []  # (proposal_id, status, pr_url, issue_url, report)
    for cfg in cfgs:
        props = spark.sql(
            f"""SELECT proposal_id, decision, rationale, edits, research_notes, source_urls, base_hash, item_ids
                FROM {fq}.ext_proposals
                WHERE page_key = :k AND status IN ('proposed', 'needs_research') AND pr_url IS NULL AND issue_url IS NULL
                ORDER BY created_at""",
            args={"k": cfg["key"]},
        ).collect()
        if not props:
            stats[cfg["key"]] = {"proposals": 0}
            continue
        ids = sorted({i for p in props for i in p.item_ids})
        # A temp view instead of an array parameter: list args are not portable across Spark Connect versions.
        spark.createDataFrame([(i,) for i in ids], "item_id STRING").createOrReplaceTempView("ext_pub_ids")
        bodies = {
            r.item_id: r.body
            for r in spark.sql(
                f"""SELECT q.item_id, q.body FROM {fq}.ext_queue q JOIN ext_pub_ids i ON q.item_id = i.item_id
                    WHERE q.page_key = :k""",
                args={"k": cfg["key"]},
            ).collect()
        }
        with pub.gh(token) as c:
            pub.check_token(c, cfg["repo"], token)
            current = pub.file_on_main(c, cfg["repo"], cfg["path"])
            if current is None:
                raise RuntimeError(f"{cfg['repo']}/{cfg['path']} not found on main")
            proposed = [p for p in props if p.decision == "edit"]
            fresh = [p for p in proposed if p.base_hash == sources.sha1(current)]
            for p in proposed:
                if p not in fresh:
                    updates.append((p.proposal_id, "stale", None, None, "page changed on main after review"))
            edits = [e for p in fresh for e in json.loads(p.edits or "[]")]
            new, applied, dropped = apply_edits(current, edits, bodies)
            pr_url = issue_url = None
            if applied:
                new = bump_basis(new, today)
                if SENSITIVE_RE.search(pub.added_lines(current, new)):
                    raise RuntimeError("sensitive pattern in added lines after edits — not publishing")
                branch = f"refresh/{today}-{run_id or datetime.now(UTC).strftime('%H%M%S')}"
                owner = cfg["repo"].split("/", 1)[0]
                existing = pub._json(
                    c.get(
                        f"/repos/{cfg['repo']}/pulls", params={"head": f"{owner}:{branch}", "state": "open"}
                    )
                )
                if existing:  # serverless retry — reuse the PR from the previous attempt
                    pr_url = existing[0]["html_url"]
                else:
                    base_sha = pub._json(c.get(f"/repos/{cfg['repo']}/git/ref/heads/main"))["object"]["sha"]
                    base_tree = pub._json(c.get(f"/repos/{cfg['repo']}/git/commits/{base_sha}"))["tree"][
                        "sha"
                    ]
                    tree = [{"path": cfg["path"], "mode": "100644", "type": "blob", "content": new}]
                    tree_sha = pub._json(
                        c.post(f"/repos/{cfg['repo']}/git/trees", json={"base_tree": base_tree, "tree": tree})
                    )["sha"]
                    msg = f"Refresh {cfg['key']} from release notes and docs changes ({today})\n\n{len(applied)} edit(s)."
                    commit_sha = pub._json(
                        c.post(
                            f"/repos/{cfg['repo']}/git/commits",
                            json={"message": msg, "tree": tree_sha, "parents": [base_sha]},
                        )
                    )["sha"]
                    ref = c.post(
                        f"/repos/{cfg['repo']}/git/refs",
                        json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
                    )
                    if ref.status_code == 422:  # branch left by a failed attempt
                        pub._json(
                            c.patch(
                                f"/repos/{cfg['repo']}/git/refs/heads/{branch}",
                                json={"sha": commit_sha, "force": True},
                            )
                        )
                    else:
                        pub._json(ref)
                    pr = pub._json(
                        c.post(
                            f"/repos/{cfg['repo']}/pulls",
                            json={
                                "title": f"[자동] 최신화 수정안 {len(applied)}건 ({today})",
                                "head": branch,
                                "base": "main",
                                "body": pr_body(
                                    cfg, applied, dropped, fresh, svg_followups(current, applied)
                                ),
                            },
                        )
                    )
                    pr_url = pr["html_url"]
            notes = [n for p in props if p.decision == "needs_research" for n in (p.research_notes or [])]
            needs = [p for p in props if p.decision == "needs_research"]
            if needs or (dropped and not applied):
                r = c.post(
                    f"/repos/{cfg['repo']}/issues",
                    json={
                        "title": f"[자동] 최신화 확인 필요 ({today})",
                        "body": issue_body(cfg, notes, dropped if not applied else [], needs or fresh),
                    },
                )
                if r.is_success:
                    issue_url = r.json()["html_url"]
                else:  # missing Issues permission must not hide the PR result
                    print(f"issue not opened ({r.status_code}): {r.text[:200]}")
            report = json.dumps(
                {"applied": len(applied), "dropped": [w for _, w in dropped]}, ensure_ascii=False
            )
            for p in fresh:
                updates.append((p.proposal_id, "pr_open" if pr_url else "dropped", pr_url, issue_url, report))
            for p in needs:
                updates.append(
                    (p.proposal_id, "issue_open" if issue_url else "needs_research", None, issue_url, None)
                )
            stats[cfg["key"]] = {
                "proposals": len(props),
                "applied": len(applied),
                "dropped": len(dropped),
                "pr_url": pr_url,
                "issue_url": issue_url,
            }
    if updates:
        spark.createDataFrame(
            updates, "proposal_id STRING, st STRING, pr STRING, issue STRING, report STRING"
        ).createOrReplaceTempView("ext_pub")
        spark.sql(f"""
            MERGE INTO {fq}.ext_proposals t USING ext_pub s ON t.proposal_id = s.proposal_id
            WHEN MATCHED THEN UPDATE SET status = s.st, pr_url = s.pr, issue_url = s.issue, report = s.report""")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True, choices=["collect", "review", "publish"])
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--config", required=True, help="path to ext_pages.json")
    ap.add_argument("--llm-endpoint", default="databricks-gpt-5-5")
    ap.add_argument("--max-items", type=int, default=25)
    ap.add_argument("--secret-scope", default="")
    ap.add_argument("--secret-key", default="")
    ap.add_argument("--job-run-id", default="")
    args = ap.parse_args()

    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    fq = f"`{args.catalog}`.`{args.schema}`"
    cfgs = load_config(args.config)
    started = datetime.now(UTC)
    stats: dict = {}
    error = None
    ensure_tables(spark, fq)
    try:
        if args.step == "collect":
            stats = step_collect(spark, fq, cfgs)
        elif args.step == "review":
            stats = step_review(spark, fq, cfgs, args.llm_endpoint, args.job_run_id, args.max_items)
        else:
            from databricks.sdk.runtime import dbutils

            token = dbutils.secrets.get(scope=args.secret_scope, key=args.secret_key).strip()
            stats = step_publish(spark, fq, cfgs, token, args.job_run_id)
        print(f"ext_{args.step}", json.dumps(stats, default=str, ensure_ascii=False))
        if args.step == "collect":
            try:
                from databricks.sdk.runtime import dbutils

                dbutils.jobs.taskValues.set(key="ext_pending", value=int(stats["pending"]))
            except Exception as e:  # noqa: BLE001 — not running inside a job
                print(f"task values not set: {e}")
    except Exception:
        error = traceback.format_exc()[-4000:]
        raise
    finally:
        spark.createDataFrame(
            [
                (
                    args.job_run_id,
                    f"ext_{args.step}",
                    started,
                    datetime.now(UTC),
                    json.dumps(stats, default=str),
                    error,
                )
            ],
            "job_run_id STRING, task STRING, started_at TIMESTAMP, finished_at TIMESTAMP, stats STRING, error STRING",
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.run_log")


def selftest() -> None:
    """Fetch the live pages and exercise the pure helpers (no Spark, no LLM, no writes)."""
    cfgs = load_config(os.path.join(os.path.dirname(os.path.abspath(_here)), "ext_pages.json"))
    with sources.http_client() as client:
        for cfg in cfgs:
            raw = client.get(raw_url(cfg)).raise_for_status().text
            p = page_record(cfg, raw)
            rv = review_html(raw)
            print(
                cfg["key"],
                "basis",
                p["basis_date"],
                "cited",
                len(p["cited_urls"]),
                "review_html",
                len(rv),
                "chars",
            )
            assert p["basis_date"] is not None, "basis date not found"
            assert "<script" not in rv.replace("<script>…(생략)…</script>", ""), (
                "script leaked into review html"
            )
            bodies = {"it1": "Pages are generally available. Curators can certify and deprecate Pages."}
            # 1) a valid edit inside a table cell
            m = re.search(r"<td>([^<]{8,60})</td>", raw)
            good = {
                "find": m.group(0),
                "replace": m.group(0).replace(m.group(1), m.group(1) + " (테스트)"),
                "evidence_quote": "Curators can certify and deprecate Pages",
                "item_id": "it1",
                "source_url": "u",
                "why_ko": "t",
            }
            # 2) edit inside the SVG, 3) quote not in source, 4) ambiguous find, 5) structure change
            svg_txt = re.search(r"<text[^>]*>([^<]{4,})</text>", raw).group(0)
            bad_svg = good | {"find": svg_txt, "replace": svg_txt.replace(">", "> X", 1)}
            bad_quote = good | {"evidence_quote": "This sentence is not in the source at all"}
            bad_dup = good | {"find": "Genie", "replace": "Genie2"}
            bad_struct = good | {"replace": good["find"] + "</td></tr></tbody></table><table><tr><td>x"}
            new, applied, dropped = apply_edits(raw, [good], bodies)
            assert len(applied) == 1 and not dropped, f"valid edit was dropped: {dropped}"
            # Each bad edit alone against the original page, with the reason it must be dropped for.
            for bad, expect in (
                (bad_svg, "svg"),
                (bad_quote, "근거"),
                (bad_dup, "번 나옴"),
                (bad_struct, "구조"),
            ):
                _, ok, why = apply_edits(raw, [bad], bodies)
                print("dropped:", why[0][1] if why else None)
                assert not ok and why and expect in why[0][1], f"expected drop for {expect!r}, got {why}"
            bumped = bump_basis(new, "2099-01-01")
            print("basis dates bumped:", len(BASIS_RE.findall(raw)), "->", bumped.count("2099-01-01"))
            assert bumped.count("2099-01-01") == len(BASIS_RE.findall(raw))
            assert structure(bumped) == structure(raw)
            prompt = build_prompt(
                cfg,
                raw,
                [
                    {
                        "item_id": "it1",
                        "source": "release_notes",
                        "published_date": "2026-11-11",
                        "url": "https://example.com",
                        "title": "t",
                        "body": bodies["it1"],
                    }
                ],
            )
            print("prompt chars", len(prompt))
    print("selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
