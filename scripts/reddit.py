#!/usr/bin/env python3
"""
Reddit harvester for scan-ai-radar.

Why this exists:
  Reddit's anonymous JSON endpoints now frequently return HTTP 403 for generic
  scripted requests. old.reddit.com search/listing HTML still works reliably
  when fetched with a stable bot-style User-Agent, so this script scrapes the
  old Reddit HTML instead of relying on .json APIs.

Examples:
  python reddit.py --subreddit LocalLLaMA --query "Claude" --sort top --time week --limit 5 --json
  python reddit.py --subreddit devops --query "OpenAI Daybreak" --sort new --time week --limit 3 --comments 2 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import quote_plus, urljoin
from urllib.request import Request, build_opener

from bs4 import BeautifulSoup


BASE = "https://old.reddit.com"
UA = "redbot/0.1 by openai-codex"


@dataclass
class SearchResult:
    title: str
    subreddit: str
    score: int | None
    comments_count: int | None
    author: str | None
    ts: str | None
    permalink: str
    url: str
    summary: str
    top_comments: list[dict]


def opener():
    return build_opener()


def fetch(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": BASE + "/",
        },
    )
    with opener().open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_int(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"(\d[\d,]*)", text)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def extract_result_cards(html: str) -> Iterable[BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("div.search-result.search-result-link"):
        yield card


def parse_comment_page(permalink: str, limit: int) -> list[dict]:
    if limit <= 0:
        return []
    html = fetch(
        urljoin(BASE, permalink)
        + f"?sort=top&depth=1&limit={max(limit * 4, 10)}"
    )
    soup = BeautifulSoup(html, "html.parser")
    out = []
    seen = set()
    for comment in soup.select("div.thing.comment"):
        cid = comment.get("data-fullname")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        author_el = comment.select_one("a.author")
        body_el = comment.select_one("div.usertext-body div.md")
        score_el = comment.select_one("span.score.unvoted")
        time_el = comment.select_one("time")
        permalink_el = comment.select_one("ul.buttons a.bylink")
        author = clean_text(author_el.get_text(strip=True) if author_el else "")
        text = clean_text(body_el.get_text(" ", strip=True) if body_el else "")
        if not text:
            continue
        if "i am a bot" in text.lower() or author.lower().endswith("bot"):
            continue
        out.append(
            {
                "author": author,
                "score": parse_int(score_el.get_text(" ", strip=True) if score_el else ""),
                "ts": time_el.get("datetime") if time_el else None,
                "permalink": urljoin(BASE, permalink_el.get("href", "")) if permalink_el else urljoin(BASE, permalink),
                "text": text[:500],
            }
        )
        if len(out) >= limit:
            break
    return out


def parse_search(html: str, comments: int, limit: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    for card in extract_result_cards(html):
        title_el = card.select_one("a.search-title")
        if not title_el:
            continue
        meta = card.select_one("div.search-result-meta")
        summary_el = card.select_one("div.search-result-body div.md")
        comments_el = card.select_one("a.search-comments")
        author_el = card.select_one("a.author")
        time_el = card.select_one("time")
        subreddit_el = card.select_one("a.search-subreddit-link")
        score_el = card.select_one("span.search-score")
        external_el = card.select_one("a.search-link")

        permalink = title_el.get("href", "")
        if permalink.startswith("/"):
            permalink = urljoin(BASE, permalink)
        elif permalink.startswith("http"):
            permalink = permalink
        else:
            permalink = urljoin(BASE, "/" + permalink)

        external_url = external_el.get("href", "").strip() if external_el else ""
        if external_url.startswith("/"):
            external_url = urljoin(BASE, external_url)
        elif not external_url:
            external_url = permalink

        rel_path = "/" + permalink.split("/", 3)[3] if permalink.startswith(BASE + "/") else permalink
        results.append(
            SearchResult(
                title=clean_text(title_el.get_text(" ", strip=True)),
                subreddit=clean_text(subreddit_el.get_text(" ", strip=True) if subreddit_el else ""),
                score=parse_int(score_el.get_text(" ", strip=True) if score_el else ""),
                comments_count=parse_int(comments_el.get_text(" ", strip=True) if comments_el else ""),
                author=clean_text(author_el.get_text(" ", strip=True) if author_el else ""),
                ts=time_el.get("datetime") if time_el else None,
                permalink=permalink,
                url=external_url,
                summary=clean_text(summary_el.get_text(" ", strip=True) if summary_el else "")[:700],
                top_comments=parse_comment_page(rel_path, comments),
            )
        )
        if len(results) >= limit:
            break
    return results


def build_search_url(subreddit: str | None, query: str, sort: str, time: str) -> str:
    q = quote_plus(query)
    if subreddit:
        return f"{BASE}/r/{subreddit}/search?q={q}&restrict_sr=on&sort={sort}&t={time}"
    return f"{BASE}/search?q={q}&sort={sort}&t={time}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subreddit", help="Subreddit name without r/")
    ap.add_argument("--query", required=True, help="Search query")
    ap.add_argument("--sort", default="top", choices=["relevance", "hot", "top", "new", "comments"])
    ap.add_argument("--time", default="week", choices=["hour", "day", "week", "month", "year", "all"])
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--comments", type=int, default=2, help="Top comments to fetch per result")
    ap.add_argument("--json", action="store_true", help="Pretty print JSON")
    args = ap.parse_args()

    url = build_search_url(args.subreddit, args.query, args.sort, args.time)
    html = fetch(url)
    results = parse_search(html, args.comments, args.limit)
    payload = {
        "query": args.query,
        "subreddit": args.subreddit,
        "sort": args.sort,
        "time": args.time,
        "count": len(results),
        "items": [r.__dict__ for r in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
