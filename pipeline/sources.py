"""Source fetchers for the training-content refresh job.

Pure Python (no Spark) so they can be tested locally:
    uv run --frozen --with httpx python pipeline/sources.py

Sources:
  - release_notes: docs.databricks.com release notes RSS (all areas in one feed)
  - blog:          databricks.com blog sitemap diff + site RSS for metadata
  - site pages:    this repo's published markdown (SUMMARY.md + pages), via raw GitHub
  - doc_change:    "Last updated" + text hash of docs pages cited by site pages
"""

from __future__ import annotations

import difflib
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime

import httpx

RELEASE_NOTES_FEED = "https://docs.databricks.com/aws/en/feed.xml"
BLOG_SITEMAP = "https://www.databricks.com/en-blog-assets/sitemap/sitemap-0.xml"
SITE_RSS = "https://www.databricks.com/feed"
USER_AGENT = "databricks-training-refresh/0.1 (+https://github.com/myPlatforms/databricks-training)"

_SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def http_client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h[1-6]>|</tr>", "\n", raw)
    text = html.unescape(_TAG_RE.sub(" ", raw))
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


# ---- Release notes ----


def _release_area(link: str) -> str:
    """'.../release-notes/product/2026/october#x' -> 'product';
    '.../ai-bi/release-notes/2026#x' -> 'ai-bi'; '.../release-notes/lakebase#x' -> 'lakebase'."""
    path = link.split("#", 1)[0].split("/aws/en/", 1)[-1]
    parts = path.strip("/").split("/")
    if parts[0] == "release-notes":
        return parts[1] if len(parts) > 1 else "release-notes"
    return parts[0]


def fetch_release_notes(client: httpx.Client) -> list[dict]:
    resp = client.get(RELEASE_NOTES_FEED)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for it in root.findall("./channel/item"):
        link = (it.findtext("link") or "").strip()
        guid = (it.findtext("guid") or link).strip()
        title = html.unescape((it.findtext("title") or "").strip())
        pub = it.findtext("pubDate")
        if not link or not title or not pub:
            continue
        body = html_to_text(it.findtext("description") or "")
        items.append(
            {
                "item_id": sha1(guid),
                "source": "release_notes",
                "area": _release_area(link),
                "url": link,
                "title": title,
                "published_date": parsedate_to_datetime(pub).date(),
                "body": body,
                "content_hash": sha1(title + "\n" + body),
            }
        )
    return items


# ---- Blog ----


def fetch_blog_sitemap(client: httpx.Client) -> list[str]:
    resp = client.get(BLOG_SITEMAP)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    return [
        loc.text.strip() for loc in root.findall(".//s:loc", _SITEMAP_NS) if loc.text and "/blog/" in loc.text
    ]


def fetch_site_rss(client: httpx.Client) -> list[dict]:
    """Recent blog posts with metadata (the feed only carries ~10 items)."""
    resp = client.get(SITE_RSS)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    posts = []
    for it in root.findall("./channel/item"):
        link = (it.findtext("link") or "").strip()
        title = html.unescape((it.findtext("title") or "").strip())
        pub = it.findtext("pubDate")
        if "/blog/" not in link or not title:
            continue
        body = html_to_text(it.findtext("description") or "")
        posts.append(
            {
                "url": link,
                "title": title,
                "published_date": parsedate_to_datetime(pub).date() if pub else None,
                "body": body,
            }
        )
    return posts


def _meta(page: str, prop: str) -> str:
    for pat in (
        rf'<meta\s+[^>]*(?:property|name)="{prop}"[^>]*content="([^"]*)"',
        rf'<meta\s+[^>]*content="([^"]*)"[^>]*(?:property|name)="{prop}"',
    ):
        m = re.search(pat, page, re.IGNORECASE)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


def fetch_blog_post(client: httpx.Client, url: str) -> dict:
    resp = client.get(url)
    resp.raise_for_status()
    page = resp.text
    title = _meta(page, "og:title") or _meta(page, "twitter:title")
    desc = _meta(page, "og:description") or _meta(page, "description")
    # JSON-LD carries ISO dates; article:published_time is "Tue, 10/27/2026 - 19:00".
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', page)
    published = m.group(1) if m else ""
    if not published:
        m2 = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", _meta(page, "article:published_time"))
        published = m2.group(1) if m2 else ""
    # Blog body lives in div.article--content (no <article> element); cut before related tags.
    start = page.find("article--content")
    if start >= 0:
        end = page.find('aria-label="Related tags', start)
        body = html_to_text("<div " + page[start : end if end > 0 else start + 300000])
    else:
        body = desc
    return {
        "url": url,
        "title": title,
        "published_date": _parse_doc_date(published) if published else None,
        "body": body[:20000],
    }


def blog_item(post: dict) -> dict:
    return {
        "item_id": sha1(post["url"]),
        "source": "blog",
        "area": "blog",
        "url": post["url"],
        "title": post.get("title") or "",
        "published_date": post.get("published_date"),
        "body": post.get("body") or "",
        "content_hash": sha1((post.get("title") or "") + "\n" + (post.get("body") or "")),
    }


# ---- Site pages (this repo) ----

_SUMMARY_LINK_RE = re.compile(r"\]\(([^)#\s]+\.md)\)")
_BASIS_RE = re.compile(r"기준일:\s*(\d{4}-\d{2}-\d{2})")
_REF_SECTION_RE = re.compile(r"(?ms)^##\s*참고 문서\s*$(.*?)(?=^##\s|\Z)")
_URL_RE = re.compile(r"\((https?://[^)\s]+)\)")


def fetch_site_pages(client: httpx.Client, raw_base: str) -> list[dict]:
    """raw_base e.g. https://raw.githubusercontent.com/<owner>/<repo>/main/docs"""
    raw_base = raw_base.rstrip("/")
    resp = client.get(f"{raw_base}/SUMMARY.md")
    resp.raise_for_status()
    paths = list(dict.fromkeys(_SUMMARY_LINK_RE.findall(resp.text)))
    pages = []
    for path in paths:
        r = client.get(f"{raw_base}/{path}")
        r.raise_for_status()
        body = r.text
        title_m = re.search(r"(?m)^#\s+(.+)$", body)
        basis_m = _BASIS_RE.search(body)
        refs = _REF_SECTION_RE.search(body)
        cited = list(dict.fromkeys(_URL_RE.findall(refs.group(1)))) if refs else []
        pages.append(
            {
                "path": path,
                "title": title_m.group(1).strip() if title_m else path,
                "chapter": path.split("/", 1)[0] if "/" in path else "",
                "basis_date": date.fromisoformat(basis_m.group(1)) if basis_m else None,
                "body": body,
                "content_hash": sha1(body),
                "cited_urls": cited,
            }
        )
    return pages


# ---- Cited docs change detection ----

_DATE_MODIFIED_RE = re.compile(r'<time\s+datetime="?(\d{4}-\d{2}-\d{2})[^>]*itemprop="?dateModified')
_LAST_UPDATED_RE = re.compile(r"Last updated on\s*(?:<[^>]+>\s*)*([A-Z][a-z]{2,8}\.? \d{1,2}, \d{4})")


def _parse_doc_date(raw: str) -> date | None:
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.replace(".", ""), fmt).date()
        except ValueError:
            continue
    return None


def fetch_doc_snapshot(client: httpx.Client, url: str) -> dict:
    """Snapshot of a docs page: its 'Last updated' date and main-content text.

    docs.databricks.com prints "Last updated on Mon DD, YYYY"; learn.microsoft.com
    carries <meta name="updated_at">. The text hash is only a fallback signal
    because page chrome can change without a content change.
    """
    resp = client.get(url)
    resp.raise_for_status()
    page = resp.text
    m = _DATE_MODIFIED_RE.search(page) or _LAST_UPDATED_RE.search(page)
    last_updated = _parse_doc_date(m.group(1)) if m else None
    if last_updated is None:
        meta = _meta(page, "updated_at") or _meta(page, "ms.date")
        last_updated = _parse_doc_date(meta[:10]) if meta else None
    main = re.search(r"(?is)<article[^>]*>(.*?)</article>", page) or re.search(
        r"(?is)<main[^>]*>(.*?)</main>", page
    )
    text = html_to_text(main.group(1) if main else page)
    title = _meta(page, "og:title") or (re.search(r"(?is)<title>(.*?)</title>", page) or [None, url])[1]
    return {
        "url": url,
        "title": html.unescape(str(title)).strip(),
        "last_updated": last_updated,
        "content_hash": sha1(text),
        "body": text[:60000],
    }


def text_diff(old: str, new: str, max_chars: int = 12000) -> str:
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), "before", "after", lineterm="", n=1)
    out = "\n".join(diff)
    return out[:max_chars]


if __name__ == "__main__":
    import sys

    raw_base = (
        sys.argv[1]
        if len(sys.argv) > 1
        else ("https://raw.githubusercontent.com/myPlatforms/databricks-training/main/docs")
    )
    with http_client() as c:
        rn = fetch_release_notes(c)
        print(
            "release_notes:", len(rn), "newest:", rn[0]["published_date"], rn[0]["area"], rn[0]["title"][:60]
        )
        sm = fetch_blog_sitemap(c)
        rss = fetch_site_rss(c)
        print("blog sitemap:", len(sm), "rss:", len(rss))
        post = fetch_blog_post(c, rss[0]["url"])
        print("blog post:", post["published_date"], post["title"][:60], len(post["body"]), "chars")
        pages = fetch_site_pages(c, raw_base)
        cited = sorted({u for p in pages for u in p["cited_urls"]})
        print("pages:", len(pages), "cited docs:", len(cited))
        for u in cited[:3] + [u for u in cited if "learn.microsoft.com" in u][:1]:
            snap = fetch_doc_snapshot(c, u)
            print("doc snapshot:", snap["url"], snap["last_updated"], len(snap["body"]), "chars")
