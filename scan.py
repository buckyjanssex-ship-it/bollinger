import os, json, math, time, urllib.request, urllib.parse
from datetime import datetime, timezone

API_KEY   = os.environ.get("TD_API_KEY", "")
GH_TOKEN  = os.environ.get("GITHUB_TOKEN", "")  # auto-provided by Actions
GIST_ID   = os.environ.get("GIST_ID", "")        # set as repo secret

TICKERS = [
    ("AAPL", ["DJ","NQ","SP"]), ("MSFT", ["DJ","NQ","SP"]),
    ("NVDA", ["NQ","SP"]),      ("AMZN", ["DJ","NQ","SP"]),
    ("META", ["NQ","SP"]),      ("TSLA", ["NQ","SP"]),
    ("GOOGL",["NQ","SP"]),      ("JPM",  ["DJ","SP"]),
    ("V",    ["DJ","SP"]),      ("UNH",  ["DJ","SP"]),
    ("XOM",  ["SP"]),           ("JNJ",  ["DJ","SP"]),
    ("WMT",  ["DJ","SP"]),      ("PG",   ["DJ","SP"]),
    ("HD",   ["DJ","SP"]),      ("CVX",  ["DJ","SP"]),
    ("MRK",  ["DJ","SP"]),      ("KO",   ["DJ","SP"]),
    ("MCD",  ["DJ","SP"]),      ("GS",   ["DJ","SP"]),
]

def update_gist(progress_data, stock_data=None):
    """Update Gist directly — no CDN cache, immediately visible."""
    if not GIST_ID or not GH_TOKEN:
        print("  [gist] GIST_ID or GITHUB_TOKEN not set, skipping")
        return
    files = {
        "progress.json": {"content": json.dumps(progress_data, separators=(",", ":"))}
    }
    if stock_data is not None:
        files["data.json"] = {"content": json.dumps(stock_data, separators=(",", ":"))}
    payload = json.dumps({"files": files}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/gists/{GIST_ID}",
        data=payload, method="PATCH",
        headers={
            "Authorization": f"token {GH_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"  [gist] updated OK ({r.status})")
    except Exception as e:
        print(f"  [gist] update failed: {e}")

def write_progress(done, total, stocks, errors, status):
    now = datetime.now(timezone.utc)
    return {
        "status": status, "done": done, "total": total,
        "successful": len(stocks), "errors": len(errors),
        "updatedAt": now.isoformat(),
        "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
    }

def fetch_batch(tickers):
    url = (f"https://api.twelvedata.com/time_series"
           f"?symbol={','.join(tickers)}&interval=1day&outputsize=25"
           f"&apikey={API_KEY}&format=JSON")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    if isinstance(data, dict) and data.get("code") and data["code"] != 200:
        raise Exception(data.get("message", "API error"))
    results = []
    entries = [(tickers[0], data)] if len(tickers) == 1 else list(data.items())
    for ticker, info in entries:
        try:
            if not info or info.get("status") == "error" or not info.get("values"):
                continue
            closes = [float(v["close"]) for v in reversed(info["values"])]
            last20 = closes[-20:]
            if len(last20) < 5: continue
            cur, prev = last20[-1], last20[-2]
            chg  = (cur - prev) / prev * 100
            sma  = sum(last20) / len(last20)
            std  = math.sqrt(sum((x-sma)**2 for x in last20) / len(last20))
            upper, lower = sma+2*std, sma-2*std
            pctB = (cur-lower)/(upper-lower) if upper != lower else 0.5
            bw   = (upper-lower)/sma*100 if sma else 0
            results.append({"ticker":ticker,"price":round(cur,2),
                "sma":round(sma,2),"upper":round(upper,2),"lower":round(lower,2),
                "pctB":round(pctB,4),"bw":round(bw,2),"chg":round(chg,2)})
        except: pass
    return results

def main():
    total, stocks, errors = len(TICKERS), [], []
    BATCH = 8

    print(f"Scanning {total} tickers, GIST_ID={'set' if GIST_ID else 'NOT SET'}")

    # Push initial state
    prog = write_progress(0, total, stocks, errors, "scanning")
    update_gist(prog)

    for i in range(0, total, BATCH):
        batch_items   = TICKERS[i:i+BATCH]
        batch_tickers = [t for t,_ in batch_items]
        tag_map       = {t: tags for t,tags in batch_items}
        try:
            results = fetch_batch(batch_tickers)
            for s in results:
                s["tags"] = tag_map.get(s["ticker"], [])
                stocks.append(s)
            print(f"  [{min(i+BATCH,total)}/{total}] OK — {len(results)} stocks")
        except Exception as e:
            errors.extend(batch_tickers)
            print(f"  [{min(i+BATCH,total)}/{total}] ERROR: {e}")

        done = min(i+BATCH, total)
        now  = datetime.now(timezone.utc)
        prog = write_progress(done, total, stocks, errors, "scanning")
        stock_data = {
            "updatedAt": now.isoformat(),
            "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
            "count": len(stocks), "errors": errors, "stocks": stocks
        }
        # Update Gist immediately — no CDN delay
        update_gist(prog, stock_data)

        if i+BATCH < total:
            print(f"  waiting 61s...")
            time.sleep(61)

    # Final
    now = datetime.now(timezone.utc)
    prog = write_progress(total, total, stocks, errors, "done")
    stock_data = {
        "updatedAt": now.isoformat(),
        "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(stocks), "errors": errors, "stocks": stocks
    }
    update_gist(prog, stock_data)

    # Also save to repo for GitHub Pages fallback
    with open("data.json","w") as f: json.dump(stock_data, f, separators=(",",":"))
    with open("progress.json","w") as f: json.dump(prog, f, separators=(",",":"))
    print(f"\nDone. {len(stocks)} stocks saved.")

if __name__ == "__main__":
    main()
