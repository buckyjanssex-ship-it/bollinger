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
            if len(closes) < 30: continue

            def calc_band(c):
                """Calculate SMA, upper, lower for a given list of closes (last 20)."""
                s   = sum(c[-20:]) / 20
                sd  = (sum((x-s)**2 for x in c[-20:]) / 20) ** 0.5
                return s, s+2*sd, s-2*sd

            # Today's band
            sma, upper, lower = calc_band(closes)
            cur  = closes[-1]
            prev = closes[-2]
            chg  = (cur - prev) / prev * 100
            bw   = (upper - lower) / sma * 100 if sma else 0

            # Yesterday's band (for crossover)
            prev_sma, _, prev_lower = calc_band(closes[:-1])

            # Crossover flags
            cross_lower = prev < prev_lower and cur >= lower
            cross_sma   = prev < prev_sma   and cur >= sma

            # ── Near-upper pattern detection ──
            # For each of the last N days, check if price was within X% of upper band
            # and stayed above SMA
            def near_upper_days(closes_all, n_days, pct_threshold):
                """
                Count how many of the last n_days had:
                  - price within pct_threshold% of upper band
                  - price above SMA (not below midline)
                Returns count of consecutive days from most recent backwards.
                """
                consecutive = 0
                for d in range(1, n_days+2):  # check enough days
                    if d >= len(closes_all): break
                    # Compute band for that day
                    end_idx = len(closes_all) - d
                    if end_idx < 20: break
                    c_slice = closes_all[:end_idx+1]
                    s, u, _ = calc_band(c_slice)
                    price_d = closes_all[end_idx]
                    dist_from_upper = (u - price_d) / u * 100
                    if dist_from_upper <= pct_threshold and price_d >= s:
                        consecutive += 1
                    else:
                        break
                return consecutive

            # Check recent near-upper streaks (looking back from yesterday, not today)
            # We check yesterday onwards to find if there WAS a streak before today's pullback
            def had_near_upper_streak(closes_all, min_days, pct_threshold, lookback=15):
                """
                Find if within the last `lookback` days (excluding today),
                there was a streak of min_days consecutive days near upper band above SMA.
                Returns (found, streak_length, days_ago_ended)
                """
                for start in range(1, lookback):
                    streak = 0
                    for d in range(start, start + min_days + 5):
                        if d >= len(closes_all): break
                        end_idx = len(closes_all) - d
                        if end_idx < 20: break
                        c_slice = closes_all[:end_idx+1]
                        s, u, _ = calc_band(c_slice)
                        price_d = closes_all[end_idx]
                        dist_from_upper = (u - price_d) / u * 100
                        if dist_from_upper <= pct_threshold and price_d >= s:
                            streak += 1
                        else:
                            if streak >= min_days:
                                return True, streak, start
                            streak = 0
                    if streak >= min_days:
                        return True, streak, start
                return False, 0, 0

            # Current price position relative to SMA
            cur_dist_sma = (cur - sma) / sma * 100  # negative = below SMA

            # Pattern 1: Had 3+ days within 2% of upper (above SMA), now near SMA (within 3%)
            had3_2pct, streak3_2, ago3_2 = had_near_upper_streak(closes, 3, 2.0)
            had5_2pct, streak5_2, ago5_2 = had_near_upper_streak(closes, 5, 2.0)
            had3_5pct, streak3_5, ago3_5 = had_near_upper_streak(closes, 3, 5.0)
            had5_5pct, streak5_5, ago5_5 = had_near_upper_streak(closes, 5, 5.0)

            near_sma_now = abs(cur_dist_sma) <= 5  # currently within 5% of SMA

            # pullback_to_sma: was near upper, now pulled back to within 5% of SMA
            pullback_3d_2pct = had3_2pct and near_sma_now
            pullback_5d_2pct = had5_2pct and near_sma_now
            pullback_3d_5pct = had3_5pct and near_sma_now
            pullback_5d_5pct = had5_5pct and near_sma_now

            # Currently near upper (for tagging)
            cur_dist_upper = (upper - cur) / upper * 100
            near_upper_2pct_3d = near_upper_days(closes, 3, 2.0) >= 3
            near_upper_2pct_5d = near_upper_days(closes, 5, 2.0) >= 5
            near_upper_5pct_3d = near_upper_days(closes, 3, 5.0) >= 3
            near_upper_5pct_5d = near_upper_days(closes, 5, 5.0) >= 5

            # ── Pullback then bounce back above SMA within 3 days ──
            # Pattern:
            # 1. Had N consecutive days near upper band above SMA (historical)
            # 2. Price then pulled back to touch/cross below SMA
            # 3. Within 3 trading days, price bounced back above SMA
            # 4. Currently above SMA (confirmed bounce)

            def bounce_after_pullback(closes_all, min_upper_days, upper_pct, lookback=20):
                """
                Detect: was near upper → pulled back to SMA → bounced above SMA within 3 days.
                Returns True if pattern is complete and price is now above SMA.
                """
                n = len(closes_all)
                if n < 30: return False

                # Step 1: scan backwards to find a near-upper streak
                for streak_end in range(2, lookback):
                    # Find streak ending at streak_end days ago
                    streak_len = 0
                    for d in range(streak_end, streak_end + min_upper_days + 5):
                        if d >= n: break
                        idx = n - d
                        if idx < 20: break
                        s, u, _ = calc_band(closes_all[:idx+1])
                        p = closes_all[idx]
                        if (u - p) / u * 100 <= upper_pct and p >= s:
                            streak_len += 1
                        else:
                            break
                    if streak_len < min_upper_days:
                        continue

                    # Step 2: after the streak, price must touch or cross below SMA
                    pullback_day = None
                    for d in range(1, streak_end):
                        idx = n - d
                        if idx < 20: break
                        s, _, _ = calc_band(closes_all[:idx+1])
                        p = closes_all[idx]
                        if p <= s * 1.03:  # touched within 3% of SMA or below
                            pullback_day = d
                            break
                    if pullback_day is None:
                        continue

                    # Step 3: within 3 days of pullback, price bounced above SMA
                    bounce_found = False
                    for d in range(1, min(pullback_day, 4)):  # up to 3 days after pullback
                        idx = n - d
                        if idx < 20: break
                        s, _, _ = calc_band(closes_all[:idx+1])
                        p = closes_all[idx]
                        if p > s:
                            bounce_found = True
                            break

                    # Step 4: current price must be above SMA
                    if bounce_found and cur > sma:
                        return True

                return False

            bounce_3d_2pct = bounce_after_pullback(closes, 3, 2.0)
            bounce_5d_2pct = bounce_after_pullback(closes, 5, 2.0)
            bounce_3d_5pct = bounce_after_pullback(closes, 3, 5.0)
            bounce_5d_5pct = bounce_after_pullback(closes, 5, 5.0)

            results.append({
                "ticker": ticker, "price": round(cur,2),
                "sma": round(sma,2), "upper": round(upper,2), "lower": round(lower,2),
                "bw": round(bw,2), "chg": round(chg,2),
                "crossLower": cross_lower,
                "crossSma":   cross_sma,
                # Currently near upper band (above SMA)
                "nearUpper2d3":  near_upper_2pct_3d,
                "nearUpper2d5":  near_upper_2pct_5d,
                "nearUpper5d3":  near_upper_5pct_3d,
                "nearUpper5d5":  near_upper_5pct_5d,
                # Was near upper, now pulled back to SMA
                "pullback3d2pct": pullback_3d_2pct,
                "pullback5d2pct": pullback_5d_2pct,
                "pullback3d5pct": pullback_3d_5pct,
                "pullback5d5pct": pullback_5d_5pct,
                # Pulled back to SMA then bounced above SMA within 3 days
                "bounce3d2pct": bounce_3d_2pct,
                "bounce5d2pct": bounce_5d_2pct,
                "bounce3d5pct": bounce_3d_5pct,
                "bounce5d5pct": bounce_5d_5pct,
            })
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
