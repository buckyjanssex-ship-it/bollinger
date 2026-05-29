import os, json, math, time, urllib.request, urllib.error
from datetime import datetime, timezone

API_KEY  = os.environ.get("TD_API_KEY", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIST_ID  = os.environ.get("GIST_ID", "")

DJ = ["AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
      "GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM","MRK",
      "MSFT","NKE","PG","SHW","TRV","UNH","V","VZ","WMT","AMZN"]

NQ = ["AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","GOOG","AVGO","COST",
      "NFLX","TMUS","AMD","QCOM","INTU","TXN","AMAT","MU","ISRG","BKNG",
      "REGN","VRTX","PANW","LRCX","ADI","MRVL","KLAC","CDNS","SNPS","ORLY",
      "CRWD","FTNT","ASML","MELI","PYPL","ADP","MAR","CTAS","TEAM","DXCM",
      "MNST","FAST","PAYX","IDXX","PCAR","ROST","ODFL","GEHC","KDP","FANG",
      "EXC","XEL","CTSH","BIIB","ILMN","DLTR","ZS","NXPI","ANSS","VRSK",
      "ON","ALGN","TTWO","LULU","SBUX","PDD","ABNB","ARM","SMCI","MSTR",
      "PLTR","HOOD","RBLX","DOCU","ZM","OKTA","DDOG","MDB","SNOW","WDAY"]

SP = [
    "NOW","HUBS","NET","TTD","COIN","SHOP","SQ","ACN","ORCL","EPAM",
    "GLOB","LDOS","BAH","SAIC","MSCI","SPGI","MCO","FIS","FISV","GPN",
    "ADSK","PTC","ANSS","PAYC","PCTY","BILL","AFRM","SOFI","UPST","INTC",
    "JPM","BAC","WFC","MS","BLK","C","AXP","SCHW","COF","USB",
    "PNC","TFC","CB","MMC","AON","MET","PRU","AFL","ALL","ICE",
    "CME","CBOE","NDAQ","RJF","TROW","BX","KKR","APO","CG","ARES",
    "UNH","LLY","JNJ","ABT","MRK","TMO","DHR","SYK","BSX","MDT",
    "EW","IQV","HCA","CNC","ELV","CI","HUM","MRNA","BNTX","GILD",
    "ALNY","NBIX","EXAS","VEEV","ZBH","BAX","STE","HOLX","PODD","BIO",
    "AMZN","COST","WMT","TGT","HD","LOW","MCD","CMG","YUM","DPZ",
    "DASH","HLT","MAR","MGM","WYNN","RCL","CCL","DAL","UAL","AAL",
    "CPRT","AZO","ORLY","GPC","TSCO","ULTA","BBY","DKS","FIVE","WSM",
    "XOM","CVX","COP","EOG","SLB","MPC","VLO","PSX","HES","DVN",
    "OXY","APA","HAL","BKR","EQT","AR","RRC","CNX","CHK","NOV",
    "CAT","DE","HON","RTX","LMT","NOC","GD","ETN","EMR","GE",
    "UPS","FDX","CSX","NSC","UNP","BA","MMM","ITW","PH","ROK",
    "AME","ROP","CARR","OTIS","TT","JCI","PWR","SWK","LHX","TDG",
    "GOOGL","META","NFLX","DIS","CMCSA","T","VZ","CHTR","EA","SNAP",
    "PINS","MTCH","LYV","PARA","FOXA","WMG","NYT","IAC","TTWO","ATVI",
    "NEE","DUK","SO","D","AEP","PCG","XEL","ES","AWK","WEC",
    "LIN","APD","SHW","ECL","NEM","FCX","NUE","VMC","ALB","BALL",
    "PKG","IP","CF","MOS","DD","PLD","AMT","EQIX","CCI","SPG",
    "O","WELL","AVB","EQR","DLR","VTR","PSA","NEE","DUK","SO",
    "D","AEP","PCG","XEL","ES","AWK","WEC","NI","ATO","LNT",
    "SPY","QQQ","IWM","DIA","XLF","XLK","XLE","XLV","XLI","XLC",
    "SOXX","ARKK","GLD","TLT","EEM","UBER","LYFT","RIVN","NIO","BIDU",
]

def build_list():
    tag_map = {}
    for t in DJ: tag_map.setdefault(t, set()).add("DJ")
    for t in NQ: tag_map.setdefault(t, set()).add("NQ")
    for t in SP: tag_map.setdefault(t, set()).add("SP")
    # Remove tickers with dots or invalid chars
    return [(t, sorted(tags)) for t, tags in tag_map.items() if '.' not in t]

def update_gist(progress_data, stock_data=None):
    if not GIST_ID or not GH_TOKEN:
        print("  [gist] GIST_ID or GITHUB_TOKEN not set, skipping")
        return
    files = {"progress.json": {"content": json.dumps(progress_data, separators=(",", ":"))}}
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
    except urllib.error.HTTPError as e:
        print(f"  [gist] HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"  [gist] error: {e}")

def write_progress(done, total, stocks, errors, status):
    now = datetime.now(timezone.utc)
    return {
        "status": status, "done": done, "total": total,
        "successful": len(stocks), "errors": len(errors),
        "updatedAt": now.isoformat(),
        "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
    }

def make_stock_data(stocks, errors):
    now = datetime.now(timezone.utc)
    return {
        "updatedAt": now.isoformat(),
        "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(stocks), "errors": errors, "stocks": stocks
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
            if len(closes) < 22: continue
            # Current day uses last 20 closes
            last20 = closes[-20:]
            cur    = last20[-1]
            prev   = last20[-2]
            chg    = (cur - prev) / prev * 100
            sma    = sum(last20) / len(last20)
            std    = math.sqrt(sum((x-sma)**2 for x in last20) / len(last20))
            upper, lower = sma+2*std, sma-2*std
            bw     = (upper-lower)/sma*100 if sma else 0
            # Previous day uses closes[-21:-1] to get yesterday's band
            prev20     = closes[-21:-1]
            prev_sma   = sum(prev20) / len(prev20)
            prev_std   = math.sqrt(sum((x-prev_sma)**2 for x in prev20) / len(prev20))
            prev_lower = prev_sma - 2*prev_std
            # Crossover flags
            cross_lower = prev < prev_lower and cur >= lower   # crossed above lower band
            cross_sma   = prev < prev_sma   and cur >= sma     # crossed above SMA
            results.append({"ticker":ticker,"price":round(cur,2),
                "sma":round(sma,2),"upper":round(upper,2),"lower":round(lower,2),
                "bw":round(bw,2),"chg":round(chg,2),
                "crossLower": cross_lower,
                "crossSma":   cross_sma})
        except: pass
    return results

def main():
    watchlist = build_list()
    tag_map   = {t: tags for t, tags in watchlist}
    tickers   = [t for t, _ in watchlist]
    total     = len(tickers)
    stocks, errors = [], []
    BATCH = 8

    print(f"=== CONFIG CHECK ===")
    print(f"  TD_API_KEY : {'SET' if API_KEY else 'NOT SET ⚠'}")
    print(f"  GIST_ID    : {'SET' if GIST_ID else 'NOT SET ⚠'}")
    print(f"  GITHUB_TOKEN: {'SET' if GH_TOKEN else 'NOT SET ⚠'}")
    print(f"  Total tickers: {total}")
    print(f"====================")

    # Reset Gist to scanning=0 immediately
    prog = write_progress(0, total, stocks, errors, "scanning")
    update_gist(prog)

    for i in range(0, total, BATCH):
        batch_tickers = tickers[i:i+BATCH]
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
        prog = write_progress(done, total, stocks, errors, "scanning")
        update_gist(prog, make_stock_data(stocks, errors))

        if i+BATCH < total:
            print(f"  waiting 61s...")
            time.sleep(61)

    # Final
    prog       = write_progress(total, total, stocks, errors, "done")
    stock_data = make_stock_data(stocks, errors)
    update_gist(prog, stock_data)

    with open("data.json",    "w") as f: json.dump(stock_data, f, separators=(",",":"))
    with open("progress.json","w") as f: json.dump(prog,       f, separators=(",",":"))
    print(f"\nDone. {len(stocks)}/{total} stocks saved, {len(errors)} errors.")

if __name__ == "__main__":
    main()
