#!/usr/bin/env python3
"""
CDP X/Twitter (and generic page) harvester for scan-ai-radar.

Drives an already-logged-in Chrome via the DevTools Protocol and extracts
content. Crucially it harvests INCREMENTALLY while scrolling, so it survives
X's virtualized timeline (off-screen <article> nodes get unmounted from the
DOM; reading only once at the end loses everything that scrolled past).

Usage:
  python3 cdp.py <url> [--port 9223] [--scrolls 12] [--step 2.2] [--wait 6]
                       [--json] [--keep] [--no-fresh]

Freshness (default ON):
  Chrome's CDP serves cached pages hard, and X aggressively caches the
  profile/search SPA, so a plain /json/new?url= often returns STALE content
  (posts from days/weeks ago). To force fresh data this tool:
    1. opens a blank tab, enables Network, and sets cacheDisabled=true
    2. navigates to the URL and waits for the load event
    3. does a Page.reload(ignoreCache=true) and scrolls to top
    4. waits for fresh <time> nodes before harvesting
  Pass --no-fresh to skip the cache-busting reload (faster, may be stale).

Notes:
  - Probe ports first (9223 then 9222). Pass the working one via --port.
  - For X search, prefer f=live (latest, time-ordered) over f=top when you
    need fresh near-window signal; f=top buries new posts under old hot ones.
  - Bypasses any http(s)_proxy when talking to the local CDP endpoint.
"""
import asyncio, json, sys, argparse, urllib.request
import websockets

def http_factory(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def http(path, method="GET"):
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method)
        return json.load(opener.open(req, timeout=10))
    return http

# In-page async harvester. Accumulates de-duped tweets across scroll steps so
# virtualization can't drop rows. Returns JSON string via returnByValue.
HARVEST_JS = r"""(async () => {
  const MAX = __MAX__, STEP = __STEP__;
  const seen = new Map();
  const norm = (href) => {
    if (!href) return null;
    let u = href.split('?')[0];
    u = u.replace(/\/(photo|analytics|history)\/?\d*$/, '');
    return u.startsWith('http') ? u : ('https://x.com' + u);
  };
  const harvest = () => {
    for (const a of document.querySelectorAll('article')) {
      const link = a.querySelector('a[href*="/status/"]');
      const url = norm(link && link.getAttribute('href'));
      const timeEl = a.querySelector('time');
      const ts = timeEl ? timeEl.getAttribute('datetime') : '';
      const text = (a.innerText || '').replace(/\s*\n+\s*/g, ' | ').slice(0, 700);
      const key = url || text.slice(0, 90);
      if (key && !seen.has(key)) seen.set(key, { url, ts, text });
    }
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  try { window.scrollTo(0, 0); } catch (e) {}
  await sleep(1500);
  const loggedOut = !!document.querySelector('a[href="/login"], a[href*="/i/flow/login"]');
  let lastH = -1, stable = 0;
  for (let i = 0; i < MAX; i++) {
    harvest();
    window.scrollBy(0, Math.round(window.innerHeight * 0.9));
    await sleep(STEP);
    const h = document.documentElement.scrollHeight;
    if (h === lastH) { stable++; if (stable >= 3) break; } else { stable = 0; }
    lastH = h;
  }
  harvest();
  const items = [...seen.values()];
  return JSON.stringify({ loggedOut, count: items.length, title: document.title, items });
})()"""

# Wait (in-page) until fresh tweet timestamps render after a cache-busting
# reload, so we never harvest the stale pre-reload DOM.
FRESH_WAIT_JS = r"""(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  try { window.scrollTo(0, 0); } catch (e) {}
  for (let i = 0; i < 25; i++) {
    if (document.querySelector('article time') ||
        document.querySelector('a[href*="/i/flow/login"]')) break;
    await sleep(400);
  }
  await sleep(800);
  return document.querySelectorAll('article').length;
})()"""

async def run(url, port, scrolls, step, wait, keep, fresh=True):
    http = http_factory(port)
    # Open a BLANK tab first so we can disable cache before the real navigation.
    try:
        t = http("/json/new?about:blank", method="PUT")
    except Exception:
        t = http("/json/new?about:blank")
    ws_url, tid = t["webSocketDebuggerUrl"], t["id"]
    out = ""
    try:
        async with websockets.connect(ws_url, max_size=None, open_timeout=20) as ws:
            i = 0
            async def cmd(method, params=None, timeout=90):
                nonlocal i
                i += 1
                mid = i
                await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
                while True:
                    r = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
                    if r.get("id") == mid:
                        return r
            await cmd("Page.enable")
            await cmd("Runtime.enable")
            await cmd("Network.enable")
            # Force every request to hit the network, not Chrome's cache.
            await cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            await cmd("Page.navigate", {"url": url})
            await asyncio.sleep(wait)  # initial load / SPA hydrate
            if fresh:
                # Hard reload bypassing cache, then wait for fresh <time> nodes.
                await cmd("Page.reload", {"ignoreCache": True})
                await asyncio.sleep(max(2.5, wait * 0.6))
                await cmd("Runtime.evaluate",
                          {"expression": FRESH_WAIT_JS, "awaitPromise": True, "returnByValue": True},
                          timeout=30)
            js = HARVEST_JS.replace("__MAX__", str(scrolls)).replace("__STEP__", str(int(step * 1000)))
            r = await cmd("Runtime.evaluate",
                          {"expression": js, "awaitPromise": True, "returnByValue": True},
                          timeout=max(60, int(scrolls * (step + 1)) + 30))
            out = r.get("result", {}).get("result", {}).get("value", "") or json.dumps(r.get("result", {}))
    finally:
        if not keep:
            try: http(f"/json/close/{tid}")
            except Exception: pass
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--port", type=int, default=9223)
    ap.add_argument("--scrolls", type=int, default=12)
    ap.add_argument("--step", type=float, default=2.2)
    ap.add_argument("--wait", type=float, default=6.0)
    ap.add_argument("--json", action="store_true", help="pretty-print the JSON result")
    ap.add_argument("--keep", action="store_true", help="do not close the tab afterwards")
    ap.add_argument("--no-fresh", action="store_true",
                    help="skip cache-busting reload (faster, may return stale content)")
    a = ap.parse_args()
    out = asyncio.run(run(a.url, a.port, a.scrolls, a.step, a.wait, a.keep, fresh=not a.no_fresh))
    if a.json:
        try:
            print(json.dumps(json.loads(out), ensure_ascii=False, indent=2))
            return
        except Exception:
            pass
    print(out)

if __name__ == "__main__":
    main()
