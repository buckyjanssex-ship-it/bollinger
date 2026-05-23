import os, json, math, time, urllib.request, urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("TD_API_KEY", "")

DJ = ["AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
      "GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM","MRK",
      "MSFT","NKE","PG","SHW","TRV","UNH","V","VZ","WMT","AMZN"]

NQ = ["AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","AVGO","COST","NFLX",
      "TMUS","AMD","QCOM","INTU","TXN","AMAT","MU","ISRG","BKNG","REGN",
      "VRTX","PANW","LRCX","ADI","MRVL","KLAC","CDNS","SNPS","ORLY","CRWD",
      "FTNT","MELI","PYPL","ADP","MAR","CTAS","TEAM","DXCM","MNST","FAST",
      "PAYX","IDXX","PCAR","ROST","ODFL","KDP","EXC","XEL","CTSH","BIIB",
      "DLTR","ZS","NXPI","ANSS","VRSK","ON","ALGN","TTWO","SMCI","MSTR"]

SP = ["AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA","AVGO","ORCL","ADBE",
      "CRM","AMD","INTC","QCOM","TXN","AMAT","MU","LRCX","KLAC","NOW",
      "SNPS","CDNS","FTNT","PANW","CRWD","JPM","BAC","WFC","GS","MS",
      "BLK","C","AXP","SCHW","COF","USB","PNC","CB","MMC","AON",
      "UNH","LLY","JNJ","ABT","MRK","TMO","DHR","ISRG","SYK","BSX",
      "MDT","EW","DXCM","IQV","IDXX","COST","WMT","TGT","HD","LOW",
      "MCD","SBUX","NKE","LULU","CMG","YUM","BKNG","HLT","MAR","ABNB",
      "XOM","CVX","COP","EOG","SLB","MPC","VLO","PSX","CAT","DE",
      "HON","RTX","LMT","NOC","GD","ETN","EMR","GE","UPS","FDX",
      "CSX","NSC","UNP","BA","MMM","NFLX","DIS","CMCSA","T","VZ",
      "TMUS","EA","NEE","DUK","SO","AEP","EXC","LIN","APD","SHW",
      "ECL","NEM","FCX","PLD","AMT","EQIX","CCI","SPG","O","DLR",
      "SPY","QQQ","IWM","XLF","XLK","XLE","XLV","XLI","SOXX","ARKK"]

def build_list():
    tag_map = {}
    for t in DJ: tag_map.setdefault(t, set()).add("DJ")
    for t in NQ: tag_map.setdefault(t, set()).add("NQ")
    for t in SP: tag_map.setdefault(t, set()).add("SP")
    return [(t, sorted(tags)) for t, tags in tag_map.items()]

def fetch_batch(tickers):
    symbols = ",".join(tickers)
    url = (f"https://api.twelvedata.com/time_series"
           f"?symbol={symbols}&interval=1day&outputsize=25"
           f"&apikey={API_KEY}&format=JSON")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    # Check top-level API error
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
            if len(last20) < 5:
                continue
            cur  = last20[-1]
            prev = last20[-2] if len(last20) > 1 else cur
            chg  = ((cur - prev) / prev * 100) if prev else 0
            sma  = sum(last20) / len(last20)
            std  = math.sqrt(sum((x - sma)**2 for x in last20) / len(last20))
            upper, lower = sma + 2*std, sma - 2*std
            pctB = (cur - lower) / (upper - lower) if upper != lower else 0.5
            bw   = (upper - lower) / sma * 100 if sma else 0
            results.append({
                "ticker": ticker, "price": round(cur, 2),
                "sma": round(sma, 2), "upper": round(upper, 2),
                "lower": round(lower, 2), "pctB": round(pctB, 4),
                "bw": round(bw, 2), "chg": round(chg, 2)
            })
        except Exception:
            pass
    return results

def main():
    watchlist = build_list()
    tag_map   = {t: tags for t, tags in watchlist}
    tickers   = [t for t, _ in watchlist]
    BATCH     = 8
    stocks    = []
    errors    = []

    print(f"Scanning {len(tickers)} tickers in batches of {BATCH}...")
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i+BATCH]
        try:
            results = fetch_batch(batch)
            for s in results:
                s["tags"] = tag_map.get(s["ticker"], [])
                stocks.append(s)
            print(f"  [{i+BATCH}/{len(tickers)}] OK — {len(results)} returned")
        except Exception as e:
            errors.extend(batch)
            print(f"  [{i+BATCH}/{len(tickers)}] ERROR: {e}")

        # Rate limit: 8 calls/min on free tier
        if i + BATCH < len(tickers):
            print("  Waiting 61s (rate limit)...")
            time.sleep(61)

    now = datetime.now(timezone.utc)
    output = {
        "updatedAt":    now.isoformat(),
        "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
        "count":        len(stocks),
        "errors":       errors,
        "stocks":       stocks
    }
    with open("data.json", "w") as f:
        json.dump(output, f, separators=(",", ":"))
    print(f"\nDone. {len(stocks)} stocks saved, {len(errors)} errors.")

if __name__ == "__main__":
    main()
