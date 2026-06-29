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
import asyncio
import json
import re
import socket
import sys
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import quote_plus, urljoin
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

from bs4 import BeautifulSoup
import websockets


BASE = "https://old.reddit.com"
BASE_WWW = "https://www.reddit.com"
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
    return build_opener(ProxyHandler({}))


def http_factory(port: int):
    op = build_opener(ProxyHandler({}))

    def http(path: str, method: str = "GET"):
        req = Request(f"http://127.0.0.1:{port}{path}", method=method)
        return json.load(op.open(req, timeout=10))

    return http


def probe_cdp_port() -> int | None:
    for port in (9223, 9222):
        try:
            info = http_factory(port)("/json/version")
        except Exception:
            continue
        if isinstance(info, dict) and info.get("Browser") and info.get("Protocol-Version"):
            return port
    return None


async def cdp_fetch(url: str, port: int, wait: float = 4.5) -> str:
    http = http_factory(port)
    try:
        tab = http("/json/new?about:blank", method="PUT")
    except Exception:
        tab = http("/json/new?about:blank")
    ws_url, tid = tab["webSocketDebuggerUrl"], tab["id"]
    try:
        async with websockets.connect(ws_url, max_size=None, open_timeout=20) as ws:
            mid = 0

            async def cmd(method: str, params: dict | None = None, timeout: float = 60):
                nonlocal mid
                mid += 1
                current = mid
                await ws.send(json.dumps({"id": current, "method": method, "params": params or {}}))
                while True:
                    resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
                    if resp.get("id") == current:
                        return resp

            await cmd("Page.enable")
            await cmd("Runtime.enable")
            await cmd("Network.enable")
            await cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            await cmd("Page.navigate", {"url": url})
            await asyncio.sleep(wait)
            result = await cmd(
                "Runtime.evaluate",
                {"expression": "document.documentElement.outerHTML", "returnByValue": True},
                timeout=30,
            )
            return result.get("result", {}).get("result", {}).get("value", "")
    finally:
        try:
            http(f"/json/close/{tid}")
        except Exception:
            pass


def fetch_via_cdp(url: str, port: int | None = None) -> str:
    actual_port = port or probe_cdp_port()
    if not actual_port:
        raise RuntimeError("Reddit HTTP fetch was blocked and no usable Chrome CDP port was found (tried 9223, 9222).")
    html = asyncio.run(cdp_fetch(url, actual_port))
    if not html:
        raise RuntimeError(f"Chrome CDP fetched an empty Reddit page via port {actual_port}.")
    return html


def fetch(url: str, cdp_port: int | None = None, allow_cdp_fallback: bool = True) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": BASE + "/",
        },
    )
    try:
        with opener().open(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "ignore")
    except HTTPError as e:
        if e.code == 403 and allow_cdp_fallback:
            return fetch_via_cdp(url.replace(BASE, BASE_WWW, 1), port=cdp_port)
        raise
    except (URLError, TimeoutError, socket.timeout):
        if allow_cdp_fallback:
            return fetch_via_cdp(url.replace(BASE, BASE_WWW, 1), port=cdp_port)
        raise


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


def parse_current_comment_page(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    seen = set()
    for comment in soup.select("shreddit-comment[thingid^='t1_']"):
        cid = comment.get("thingid")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        text_el = comment.select_one("[slot='comment'] div[id$='-post-rtjson-content']")
        text = clean_text(text_el.get_text(" ", strip=True) if text_el else "")
        if not text:
            continue
        author = clean_text(comment.get("author", ""))
        if "i am a bot" in text.lower() or author.lower().endswith("bot"):
            continue
        permalink = comment.get("permalink", "")
        out.append(
            {
                "author": author,
                "score": parse_int(comment.get("score")),
                "ts": comment.get("created"),
                "permalink": urljoin(BASE_WWW, permalink) if permalink else None,
                "text": text[:500],
            }
        )
        if len(out) >= limit:
            break
    return out


def parse_comment_page(permalink: str, limit: int, cdp_port: int | None = None) -> list[dict]:
    if limit <= 0:
        return []
    url = urljoin(BASE, permalink) + f"?sort=top&depth=1&limit={max(limit * 4, 10)}"
    html = fetch(url, cdp_port=cdp_port)
    if "shreddit-comment" in html:
        return parse_current_comment_page(html, limit)

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


def parse_current_search(html: str, comments: int, limit: int, cdp_port: int | None = None) -> list[SearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[SearchResult] = []
    for card in soup.select("search-telemetry-tracker[consume-events='post/consume/post']"):
        meta = {}
        raw_meta = card.get("data-faceplate-tracking-context")
        if raw_meta:
            try:
                meta = json.loads(raw_meta)
            except json.JSONDecodeError:
                meta = {}

        title_el = card.select_one("a[data-testid='post-title-text']")
        permalink = title_el.get("href", "") if title_el else ""
        if not permalink:
            continue

        subreddit_name = (
            meta.get("subreddit", {}).get("name")
            or clean_text(card.select_one(".post-credit-row a[href*='/r/']").get_text(" ", strip=True) if card.select_one(".post-credit-row a[href*='/r/']") else "")
        )
        author = meta.get("profile", {}).get("name") or ""
        time_el = card.select_one("time")
        counter = clean_text(card.select_one("[data-testid='search-counter-row']").get_text(" ", strip=True) if card.select_one("[data-testid='search-counter-row']") else "")
        score = parse_int(counter)
        comments_count = parse_int(counter.split("comments")[0].split("·")[-1] if "comments" in counter and "·" in counter else counter)
        summary_el = card.select_one("a.relative.text-14")
        summary = clean_text(summary_el.get_text(" ", strip=True) if summary_el else "")

        results.append(
            SearchResult(
                title=clean_text(title_el.get_text(" ", strip=True)),
                subreddit=clean_text(subreddit_name),
                score=score,
                comments_count=comments_count,
                author=clean_text(author),
                ts=time_el.get("datetime") if time_el else None,
                permalink=urljoin(BASE_WWW, permalink),
                url=urljoin(BASE_WWW, permalink),
                summary=summary[:700],
                top_comments=parse_comment_page(permalink, comments, cdp_port=cdp_port),
            )
        )
        if len(results) >= limit:
            break
    return results


def parse_search(html: str, comments: int, limit: int, cdp_port: int | None = None) -> list[SearchResult]:
    if "search-telemetry-tracker" in html and "data-testid=\"search-sdui-post\"" in html:
        return parse_current_search(html, comments, limit, cdp_port=cdp_port)

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
                top_comments=parse_comment_page(rel_path, comments, cdp_port=cdp_port),
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
    ap.add_argument("--cdp-port", type=int, help="Chrome CDP port for browser fallback (default: auto probe 9223 -> 9222)")
    ap.add_argument("--no-cdp-fallback", action="store_true", help="Do not use Chrome CDP when anonymous Reddit fetch returns HTTP 403")
    ap.add_argument("--json", action="store_true", help="Pretty print JSON")
    args = ap.parse_args()

    url = build_search_url(args.subreddit, args.query, args.sort, args.time)
    html = fetch(url, cdp_port=args.cdp_port, allow_cdp_fallback=not args.no_cdp_fallback)
    results = parse_search(html, args.comments, args.limit, cdp_port=args.cdp_port)
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
