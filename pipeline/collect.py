"""Task 1 (collect) — fetch sources and upsert into Delta.

Tables (in <catalog>.<schema>):
  source_items   one row per release note / blog post / cited-doc change
  pages          current published pages of the site
  doc_snapshots  history of cited docs pages (Last updated + text)
  run_log        one row per task run

Items published before --since (or seen on the first run of a source) are stored
with status='baseline' and never classified; newer ones get status='new'.

Job usage (spark_python_task parameters):
  --catalog C --schema S --site-raw-base URL --since YYYY-MM-DD [--blog-fetch-cap N]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import UTC, date, datetime

# Serverless spark_python_task runs the file via exec() without __file__; argv[0] is the path.
_here = (
    globals().get("__file__")
    or globals().get("filename")  # set by the serverless exec() wrapper
    or (sys.argv[0] if sys.argv and sys.argv[0].endswith(".py") else "")
)
sys.path.insert(0, os.path.dirname(os.path.abspath(_here)) if _here else os.getcwd())

import sources
from pyspark.sql import SparkSession
from pyspark.sql import types as T

ITEM_SCHEMA = T.StructType(
    [
        T.StructField("item_id", T.StringType()),
        T.StructField("source", T.StringType()),
        T.StructField("area", T.StringType()),
        T.StructField("url", T.StringType()),
        T.StructField("title", T.StringType()),
        T.StructField("published_date", T.DateType()),
        T.StructField("body", T.StringType()),
        T.StructField("content_hash", T.StringType()),
        T.StructField("status", T.StringType()),
    ]
)
PAGE_SCHEMA = T.StructType(
    [
        T.StructField("path", T.StringType()),
        T.StructField("title", T.StringType()),
        T.StructField("chapter", T.StringType()),
        T.StructField("basis_date", T.DateType()),
        T.StructField("body", T.StringType()),
        T.StructField("content_hash", T.StringType()),
        T.StructField("cited_urls", T.ArrayType(T.StringType())),
    ]
)
SNAPSHOT_SCHEMA = T.StructType(
    [
        T.StructField("url", T.StringType()),
        T.StructField("title", T.StringType()),
        T.StructField("last_updated", T.DateType()),
        T.StructField("content_hash", T.StringType()),
        T.StructField("body", T.StringType()),
    ]
)


def ensure_tables(spark: SparkSession, fq: str) -> None:
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.source_items (
          item_id STRING NOT NULL, source STRING, area STRING, url STRING, title STRING,
          published_date DATE, body STRING, content_hash STRING,
          status STRING COMMENT 'baseline | new | classified | error',
          first_seen_at TIMESTAMP, last_seen_at TIMESTAMP)
        COMMENT 'Training refresh: collected release notes, blog posts, cited-doc changes'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.pages (
          path STRING NOT NULL, title STRING, chapter STRING, basis_date DATE, body STRING,
          content_hash STRING, cited_urls ARRAY<STRING>, fetched_at TIMESTAMP)
        COMMENT 'Training refresh: current published site pages'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.doc_snapshots (
          url STRING NOT NULL, title STRING, last_updated DATE, content_hash STRING, body STRING,
          fetched_at TIMESTAMP)
        COMMENT 'Training refresh: snapshot history of docs pages cited by the site'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.item_page_map (
          item_id STRING NOT NULL, relevant BOOLEAN, change_type STRING, chapter STRING,
          pages ARRAY<STRING>, new_page_candidate STRING, summary_ko STRING, reason STRING,
          model STRING, classified_at TIMESTAMP)
        COMMENT 'Training refresh: LLM classification of source items to site pages'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.revision_proposals (
          proposal_id STRING NOT NULL, item_ids ARRAY<STRING>, page_path STRING,
          change_type STRING, rationale STRING, proposed_markdown STRING,
          source_urls ARRAY<STRING>, status STRING COMMENT 'proposed | applied | rejected',
          conversation_url STRING, pr_url STRING, created_at TIMESTAMP)
        COMMENT 'Training refresh: page revision proposals written by the Genie Code task'""")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {fq}.run_log (
          job_run_id STRING, task STRING, started_at TIMESTAMP, finished_at TIMESTAMP,
          stats STRING, error STRING)
        COMMENT 'Training refresh: per-task run log'""")


def merge_items(spark: SparkSession, fq: str, rows: list[dict]) -> int:
    """Insert unseen items; refresh last_seen_at and content of changed ones.

    Returns the number of rows inserted with status='new'.
    """
    if not rows:
        return 0
    df = spark.createDataFrame(rows, ITEM_SCHEMA)
    df.createOrReplaceTempView("incoming_items")
    before = spark.sql(f"SELECT count(*) c FROM {fq}.source_items WHERE status='new'").first().c
    spark.sql(f"""
        MERGE INTO {fq}.source_items t
        USING incoming_items s ON t.item_id = s.item_id
        WHEN MATCHED AND t.content_hash <> s.content_hash THEN UPDATE SET
          title = s.title, body = s.body, content_hash = s.content_hash,
          last_seen_at = current_timestamp()
        WHEN MATCHED THEN UPDATE SET last_seen_at = current_timestamp()
        WHEN NOT MATCHED THEN INSERT
          (item_id, source, area, url, title, published_date, body, content_hash, status,
           first_seen_at, last_seen_at)
          VALUES (s.item_id, s.source, s.area, s.url, s.title, s.published_date, s.body,
           s.content_hash, s.status, current_timestamp(), current_timestamp())""")
    after = spark.sql(f"SELECT count(*) c FROM {fq}.source_items WHERE status='new'").first().c
    return after - before


def collect_release_notes(spark, fq, client, since: date) -> dict:
    items = sources.fetch_release_notes(client)
    if not items:
        raise RuntimeError("release notes feed returned 0 items — parser or feed changed")
    for it in items:
        it["status"] = "new" if it["published_date"] >= since else "baseline"
    return {"fetched": len(items), "new": merge_items(spark, fq, items)}


def collect_blog(spark, fq, client, since: date, fetch_cap: int) -> dict:
    sitemap = sources.fetch_blog_sitemap(client)
    if not sitemap:
        raise RuntimeError("blog sitemap returned 0 URLs")
    known = {r.url for r in spark.sql(f"SELECT url FROM {fq}.source_items WHERE source='blog'").collect()}
    first_run = not known
    rss = {p["url"]: p for p in sources.fetch_site_rss(client)}
    rows, errors = [], 0
    unseen = [u for u in sitemap if u not in known]
    if first_run:
        # Baseline: record every current URL without fetching it.
        for u in unseen:
            rows.append(
                sources.blog_item({"url": u, "title": rss.get(u, {}).get("title", "")})
                | {"status": "baseline"}
            )
        unseen = [u for u in rss if u in set(sitemap)]
    for u in unseen[:fetch_cap]:
        try:
            post = sources.fetch_blog_post(client, u)
            if not post.get("title") and u in rss:
                post["title"] = rss[u]["title"]
        except Exception as e:  # noqa: BLE001 — keep going; one bad page must not fail the run
            errors += 1
            print(f"blog fetch failed {u}: {e}")
            continue
        pub = post.get("published_date")
        status = "new" if (pub is None or pub >= since) else "baseline"
        rows = [r for r in rows if r["url"] != u]
        rows.append(sources.blog_item(post) | {"status": status})
        time.sleep(0.3)
    # Row for a URL may already exist as baseline (first run) — MERGE updates content only.
    return {
        "sitemap": len(sitemap),
        "unseen": len(unseen),
        "fetched": min(len(unseen), fetch_cap),
        "errors": errors,
        "new": merge_items(spark, fq, rows),
        "first_run": first_run,
    }


def collect_pages(spark, fq, client, raw_base: str) -> list[dict]:
    pages = sources.fetch_site_pages(client, raw_base)
    if not pages:
        raise RuntimeError("site SUMMARY.md listed 0 pages")
    spark.createDataFrame(pages, PAGE_SCHEMA).createOrReplaceTempView("incoming_pages")
    # Full refresh: pages removed from the site disappear from the table.
    spark.sql(f"""
        INSERT OVERWRITE {fq}.pages
        SELECT path, title, chapter, basis_date, body, content_hash, cited_urls, current_timestamp()
        FROM incoming_pages""")
    return pages


def _is_docs_leaf(url: str) -> bool:
    """Skip site roots (e.g. https://docs.databricks.com/aws/en/) — they change constantly."""
    path = url.split("://", 1)[-1].split("#", 1)[0].rstrip("/")
    return path.count("/") >= 3


def collect_doc_changes(spark, fq, client, pages: list[dict]) -> dict:
    cited: dict[str, list[str]] = {}
    for p in pages:
        for u in p["cited_urls"]:
            u = u.split("#", 1)[0]
            if _is_docs_leaf(u) and ("docs.databricks.com" in u or "learn.microsoft.com" in u):
                cited.setdefault(u, []).append(p["path"])
    prev = {
        r.url: r
        for r in spark.sql(f"""
            SELECT url, last_updated, content_hash, body FROM (
              SELECT *, row_number() OVER (PARTITION BY url ORDER BY fetched_at DESC) rn
              FROM {fq}.doc_snapshots) WHERE rn = 1""").collect()
    }
    snaps, items, errors = [], [], 0
    for url, citing in cited.items():
        try:
            s = sources.fetch_doc_snapshot(client, url)
        except Exception as e:  # noqa: BLE001 — one bad page must not fail the run
            errors += 1
            print(f"doc fetch failed {url}: {e}")
            continue
        snaps.append({k: s[k] for k in ("url", "title", "last_updated", "content_hash", "body")})
        old = prev.get(url)
        if old is None:
            continue  # first snapshot = baseline
        date_changed = s["last_updated"] is not None and s["last_updated"] != old.last_updated
        text_changed = s["last_updated"] is None and s["content_hash"] != old.content_hash
        if date_changed or text_changed:
            diff = sources.text_diff(old.body or "", s["body"])
            if not diff.strip():
                continue
            items.append(
                {
                    "item_id": sources.sha1(f"{url}|{s['last_updated']}|{s['content_hash']}"),
                    "source": "doc_change",
                    "area": "docs",
                    "url": url,
                    "title": s["title"],
                    "published_date": s["last_updated"] or date.today(),
                    "body": "Cited by: " + ", ".join(citing) + "\n\n" + diff,
                    "content_hash": s["content_hash"],
                    "status": "new",
                }
            )
        time.sleep(0.2)
    if snaps:
        spark.createDataFrame(snaps, SNAPSHOT_SCHEMA).createOrReplaceTempView("incoming_snaps")
        spark.sql(f"""
            INSERT INTO {fq}.doc_snapshots
            SELECT url, title, last_updated, content_hash, body, current_timestamp() FROM incoming_snaps""")
    return {
        "cited": len(cited),
        "snapshots": len(snaps),
        "errors": errors,
        "new": merge_items(spark, fq, items),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--site-raw-base", required=True)
    ap.add_argument("--since", required=True, help="YYYY-MM-DD; older items are baseline")
    ap.add_argument("--blog-fetch-cap", type=int, default=40)
    ap.add_argument("--job-run-id", default="")
    args = ap.parse_args()

    spark = SparkSession.builder.getOrCreate()
    fq = f"`{args.catalog}`.`{args.schema}`"
    since = date.fromisoformat(args.since)
    started = datetime.now(UTC)
    stats: dict = {}
    error = None
    ensure_tables(spark, fq)
    try:
        with sources.http_client() as client:
            stats["release_notes"] = collect_release_notes(spark, fq, client, since)
            print("release_notes", stats["release_notes"])
            stats["blog"] = collect_blog(spark, fq, client, since, args.blog_fetch_cap)
            print("blog", stats["blog"])
            pages = collect_pages(spark, fq, client, args.site_raw_base)
            stats["pages"] = len(pages)
            stats["doc_change"] = collect_doc_changes(spark, fq, client, pages)
            print("doc_change", stats["doc_change"])
    except Exception:
        error = traceback.format_exc()[-4000:]
        raise
    finally:
        spark.createDataFrame(
            [(args.job_run_id, "collect", started, datetime.now(UTC), json.dumps(stats, default=str), error)],
            "job_run_id STRING, task STRING, started_at TIMESTAMP, finished_at TIMESTAMP, stats STRING, error STRING",
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.run_log")


if __name__ == "__main__":
    main()
