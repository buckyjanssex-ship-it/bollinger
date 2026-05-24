import os, json, math, time, urllib.request
from datetime import datetime, timezone

API_KEY = os.environ.get("TD_API_KEY", "")

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

SP = ["NOW","HUBS","NET","GTLB","PATH","CFLT","TTD","ROKU","U","COIN",
      "SHOP","SQ","BILL","PCTY","PAYC","ACN","ORCL","EPAM","GLOB","LDOS",
      "BAH","SAIC","MSCI","SPGI","MCO","FIS","FISV","GPN","WEX","AFRM",
      "ADSK","ANSS","CDNS","PTC","AZPN","JPM","BAC","WFC","MS","BLK",
      "C","AXP","SCHW","COF","USB","PNC","TFC","CB","MMC","AON",
      "MET","PRU","AFL","ALL","ICE","CME","CBOE","NDAQ","RJF","BEN",
      "IVZ","AMG","TROW","BX","KKR","APO","CG","ARES","BAM","NTRS",
      "STT","BK","ZION","CFG","UNH","LLY","JNJ","ABT","MRK","TMO",
      "DHR","SYK","BSX","MDT","EW","IQV","BIO","HOLX","PODD","HCA",
      "CNC","ELV","CI","HUM","MOH","MRNA","BNTX","GILD","ALNY","NBIX",
      "EXAS","NTRA","VEEV","ZBH","BAX","STE","PRGO","TEVA","AMZN","COST",
      "WMT","TGT","HD","LOW","MCD","CMG","YUM","DPZ","DASH","HLT",
      "MAR","MGM","WYNN","LVS","RCL","CCL","DAL","UAL","AAL","LUV",
      "CPRT","AZO","GPC","LKQ","TSCO","ULTA","BBY","DKS","FIVE","WSM",
      "RH","XOM","CVX","COP","EOG","SLB","MPC","VLO","PSX","HES",
      "DVN","OXY","APA","HAL","BKR","CHK","RRC","AR","EQT","CNX",
      "CAT","DE","HON","RTX","LMT","NOC","GD","ETN","EMR","GE",
      "UPS","FDX","CSX","NSC","UNP","BA","MMM","ITW","PH","ROK",
      "AME","ROP","XYL","CARR","OTIS","TT","JCI","GNRC","PWR","MTZ",
      "SWK","SNA","IR","TDY","HEI","TXT","HII","LHX","TDG","AXON",
      "GOOGL","META","NFLX","DIS","CMCSA","T","VZ","CHTR","EA","SNAP",
      "PINS","MTCH","LYV","WMG","PARA","FOX","FOXA","NYT","NEE","DUK",
      "SO","D","AEP","PCG","XEL","ES","AWK","WEC","CMS","NI",
      "ATO","LNT","LIN","APD","SHW","ECL","DD","NEM","FCX","NUE",
      "VMC","MLM","ALB","BALL","PKG","IP","HUN","RPM","CF","MOS",
      "PLD","AMT","EQIX","CCI","SPG","O","WELL","AVB","EQR","DLR",
      "VTR","BXP","KIM","NNN","ARE","HST","EXR","PSA","SPY","QQQ",
      "IWM","DIA","XLF","XLK","XLE","XLV","XLI","XLC","SOXX","ARKK",
      "GLD","TLT","EEM","UBER","LYFT","RIVN","NIO","BIDU","OPEN","SOFI"]

def build_list():
    tag_map = {}
    for t in DJ:  tag_map.setdefault(t, set()).add("DJ")
    for t in NQ:  tag_map.setdefault(t, set()).add("NQ")
    for t in SP:  tag_map.setdefault(t, set()).add("SP")
    return [(t, sorted(tags)) for t, tags in tag_map.items()]

def write_progress(done, total, stocks, errors, status="scanning"):
    now = datetime.now(timezone.utc)
    with open("progress.json", "w") as f:
        json.dump({
            "status":       status,
            "done":         done,
            "total":        total,
            "successful":   len(stocks),
            "errors":       len(errors),
            "updatedAt":    now.isoformat(),
            "updatedAtStr": now.strftime("%Y-%m-%d %H:%M UTC"),
        }, f, separators=(",", ":"))

def fetch_batch(tickers):
    symbols = ",".join(tickers)
    url = (f"https://api.twelvedata.com/time_series"
           f"?symbol={symbols}&interval=1day&outputsize=25"
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
    total     = len(tickers)

    print(f"Scanning {total} tickers in batches of {BATCH}...")
    write_progress(0, total, stocks, errors, "scanning")

    for i in range(0, total, BATCH):
        batch = tickers[i:i+BATCH]
        try:
            results = fetch_batch(batch)
            for s in results:
                s["tags"] = tag_map.get(s["ticker"], [])
                stocks.append(s)
            print(f"  [{min(i+BATCH,total)}/{total}] OK — {len(results)} returned")
        except Exception as e:
            errors.extend(batch)
            print(f"  [{min(i+BATCH,total)}/{total}] ERROR: {e}")

        done = min(i + BATCH, total)
        write_progress(done, total, stocks, errors, "scanning")

        if i + BATCH < total:
            print("  Waiting 61s (rate limit 8 calls/min)...")
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

    write_progress(total, total, stocks, errors, "done")
    print(f"\nDone. {len(stocks)} stocks saved, {len(errors)} errors.")

if __name__ == "__main__":
    main()
