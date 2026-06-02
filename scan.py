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
    "PINS","MTCH","LYV","PARA","FOXA","WMG","NYT","TTWO","ATVI",
    "NEE","DUK","SO","D","AEP","PCG","XEL","ES","AWK","WEC",
    "CMS","NI","ATO","LNT","LIN","APD","SHW","ECL","NEM","FCX",
    "NUE","VMC","ALB","BALL","PKG","IP","CF","MOS","DD",
    "PLD","AMT","EQIX","CCI","SPG","O","WELL","AVB","EQR","DLR",
    "VTR","PSA","NEE","SPY","QQQ","IWM","DIA","XLF","XLK","XLE",
    "XLV","XLI","SOXX","ARKK","GLD","TLT","EEM","UBER","LYFT","RIVN",
]

def build_list():
    tag_map = {}
    for t in DJ: tag_map.setdefault(t, set()).add("DJ")
    for t in NQ: tag_map.setdefault(t, set()).add("NQ")
    for t in SP: tag_map.setdefault(t, set()).add("SP")
    return [(t, sorted(tags)) for t, tags in tag_map.items() if '.' not in t]

def update_gist(progress_data, stock_data=None):
    if not GIST_ID or not GH_TOKEN:
        print("  [gist] not configured, skipping")
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

# ── Technical helpers ──

def calc_band(closes_20):
    sma = sum(closes_20) / len(closes_20)
    std = math.sqrt(sum((x - sma) ** 2 for x in closes_20) / len(closes_20))
    return sma, sma + 2 * std, sma - 2 * std

def band_at(closes_all, day_idx):
    """Band for a specific day index (0-based from start of array)."""
    if day_idx < 19: return None, None, None
    return calc_band(closes_all[day_idx-19:day_idx+1])

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return e

def calc_macd_series(closes):
    """Returns lists of (macd, signal, hist) aligned to the same day index."""
    if len(closes) < 35:
        return [], [], []
    macd_line = []
    for i in range(25, len(closes)):
        fast = ema(closes[i-11:i+1], 12)
        slow = ema(closes[i-25:i+1], 26)
        macd_line.append(fast - slow)
    if len(macd_line) < 9:
        return macd_line, [], []
    signal_line = []
    for i in range(8, len(macd_line)):
        signal_line.append(ema(macd_line[i-8:i+1], 9))
    hist = [m - s for m, s in zip(macd_line[8:], signal_line)]
    return macd_line, signal_line, hist

def detect_patterns(closes):
    """
    Returns dict of all pattern flags for a stock.

    Key conditions:
    - pullback_setup: 5 days before touching SMA, ALL above SMA, >=3 within 5% of upper
    - pullback_to_sma: setup found AND (yesterday or today touched/is near SMA)
    - bounce_from_sma: setup found AND yesterday <= SMA*1.01 AND today > SMA
    - near_upper_Nd_Xpct: currently N consecutive days within X% of upper, above SMA
    - bullish_div: price lower low, MACD hist higher low (last 10 bars)
    - bearish_div: price higher high, MACD hist lower high
    - macd_cross_up / macd_cross_down: MACD line crossed signal today
    """
    n = len(closes)
    result = {}

    # Today's band
    sma, upper, lower = calc_band(closes[-20:])
    cur  = closes[-1]
    prev = closes[-2]
    chg  = (cur - prev) / prev * 100
    bw   = (upper - lower) / sma * 100

    result.update({
        "sma": round(sma, 2), "upper": round(upper, 2), "lower": round(lower, 2),
        "chg": round(chg, 2), "bw": round(bw, 2),
    })

    # Yesterday's band
    y_sma, y_upper, y_lower = band_at(closes, n - 2) or (sma, upper, lower)

    # ── Crossover ──
    result["crossLower"] = prev < y_lower and cur >= lower
    result["crossSma"]   = prev < y_sma   and cur >= sma

    # ── Pre-pullback setup check ──
    # Find a day d_ago (1..20) where price touched/crossed below SMA
    # Then verify the 5 days IMMEDIATELY before that day:
    #   - all 5 closes > SMA on that day
    #   - >= 3 of 5 closes within 5% of upper band on that day

    def has_valid_setup(closes_all, lookback=20):
        """
        Scan backwards to find a pullback day, verify 5-day setup before it.
        Returns (found, pullback_day_ago, prev_touched) where prev_touched means
        the pullback day is yesterday (day_ago == 1).
        """
        nn = len(closes_all)
        for d_ago in range(1, lookback + 1):
            pb_idx = nn - 1 - d_ago   # absolute index of pullback day
            if pb_idx < 25: break
            s_pb, u_pb, _ = band_at(closes_all, pb_idx)
            if s_pb is None: break
            p_pb = closes_all[pb_idx]
            # Pullback day: price touched or went below SMA (within 1%)
            if p_pb > s_pb * 1.01:
                continue
            # Check 5 days before pullback day
            all_above  = True
            near_upper = 0
            for k in range(1, 6):
                check_idx = pb_idx - k
                if check_idx < 19:
                    all_above = False
                    break
                s_k, u_k, _ = band_at(closes_all, check_idx)
                if s_k is None:
                    all_above = False
                    break
                p_k = closes_all[check_idx]
                if p_k <= s_k:          # must be above SMA
                    all_above = False
                    break
                dist = (u_k - p_k) / u_k * 100
                if dist <= 5.0:         # within 5% of upper
                    near_upper += 1
            if all_above and near_upper >= 3:
                return True, d_ago
        return False, -1

    found_setup, pb_d_ago = has_valid_setup(closes)

    # pullback_to_sma: setup found, and yesterday or today is touching/near SMA
    yesterday_near_sma = prev <= y_sma * 1.01   # yesterday touched/below SMA
    today_near_sma     = cur  <= sma  * 1.02    # today still near/below SMA
    result["pullbackToSma"] = found_setup and (yesterday_near_sma or today_near_sma)

    # bounce_from_sma: setup found, yesterday touched SMA, today bounced above SMA
    result["bounceFromSma"] = (
        found_setup and
        yesterday_near_sma and  # yesterday at or below SMA
        cur > sma               # today recovered above SMA
    )

    # ── Currently near upper band ──
    def near_upper_streak(closes_all, min_days, pct):
        count = 0
        nn = len(closes_all)
        for d in range(1, min_days + 1):
            idx = nn - d
            if idx < 19: break
            s, u, _ = band_at(closes_all, idx)
            if s is None: break
            p = closes_all[idx]
            if p > s and (u - p) / u * 100 <= pct:
                count += 1
            else:
                break
        return count >= min_days

    result["nearUpper3d2pct"] = near_upper_streak(closes, 3, 2.0)
    result["nearUpper5d2pct"] = near_upper_streak(closes, 5, 2.0)
    result["nearUpper3d5pct"] = near_upper_streak(closes, 3, 5.0)
    result["nearUpper5d5pct"] = near_upper_streak(closes, 5, 5.0)

    # ── MACD ──
    macd_line, signal_line, hist = calc_macd_series(closes)
    macd_now   = macd_line[-1]   if len(macd_line)   >= 2 else 0
    macd_prev  = macd_line[-2]   if len(macd_line)   >= 2 else 0
    sig_now    = signal_line[-1] if len(signal_line)  >= 2 else 0
    sig_prev   = signal_line[-2] if len(signal_line)  >= 2 else 0
    hist_now   = hist[-1]        if len(hist)         >= 2 else 0
    hist_prev  = hist[-2]        if len(hist)         >= 2 else 0

    result["macd"]       = round(macd_now, 4)
    result["macdSignal"] = round(sig_now, 4)
    result["macdHist"]   = round(hist_now, 4)
    result["macdHistPrev"] = round(hist_prev, 4)

    # MACD crossover
    result["macdCrossUp"]   = macd_prev < sig_prev and macd_now >= sig_now
    result["macdCrossDown"] = macd_prev > sig_prev and macd_now <= sig_now

    # Bullish divergence: price made lower low vs 10 bars ago, but MACD hist made higher low
    # Look at last 10 bars for local lows
    if len(hist) >= 10 and len(closes) >= 10:
        price_window = closes[-10:]
        hist_window  = hist[-10:]
        # Find lowest price in window (excluding today)
        min_price_prev = min(price_window[:-1])
        min_hist_prev  = min(hist_window[:-1])
        # Bullish: price lower than previous low, but hist higher than previous hist low
        result["bullishDiv"] = (
            closes[-1] < min_price_prev and   # price made new low
            hist[-1] > min_hist_prev and      # MACD hist did not make new low
            hist_now < 0                       # MACD below zero (still bearish territory)
        )
        # Bearish: price higher high, MACD hist lower high
        max_price_prev = max(price_window[:-1])
        max_hist_prev  = max(hist_window[:-1])
        result["bearishDiv"] = (
            closes[-1] > max_price_prev and   # price made new high
            hist[-1] < max_hist_prev and      # MACD hist did not make new high
            hist_now > 0                       # MACD above zero
        )
    else:
        result["bullishDiv"]  = False
        result["bearishDiv"]  = False

    return result

def fetch_batch(tickers):
    url = (f"https://api.twelvedata.com/time_series"
           f"?symbol={','.join(tickers)}&interval=1day&outputsize=40"
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
            if len(closes) < 35:
                continue
            cur  = closes[-1]
            patterns = detect_patterns(closes)
            results.append({
                "ticker": ticker,
                "price":  round(cur, 2),
                **patterns
            })
        except Exception as e:
            print(f"    [{ticker}] parse error: {e}")
    return results

def main():
    watchlist = build_list()
    tag_map   = {t: tags for t, tags in watchlist}
    tickers   = [t for t, _ in watchlist]
    total     = len(tickers)
    stocks, errors = [], []
    BATCH = 8

    print(f"=== CONFIG CHECK ===")
    print(f"  TD_API_KEY  : {'SET' if API_KEY  else 'NOT SET ⚠'}")
    print(f"  GIST_ID     : {'SET' if GIST_ID  else 'NOT SET ⚠'}")
    print(f"  GITHUB_TOKEN: {'SET' if GH_TOKEN else 'NOT SET ⚠'}")
    print(f"  Total tickers: {total}")
    print(f"====================")

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

        done = min(i + BATCH, total)
        prog = write_progress(done, total, stocks, errors, "scanning")
        update_gist(prog, make_stock_data(stocks, errors))

        if i + BATCH < total:
            print(f"  waiting 61s...")
            time.sleep(61)

    prog       = write_progress(total, total, stocks, errors, "done")
    stock_data = make_stock_data(stocks, errors)
    update_gist(prog, stock_data)

    with open("data.json",     "w") as f: json.dump(stock_data, f, separators=(",", ":"))
    with open("progress.json", "w") as f: json.dump(prog,       f, separators=(",", ":"))
    print(f"\nDone. {len(stocks)}/{total} stocks, {len(errors)} errors.")

if __name__ == "__main__":
    main()
