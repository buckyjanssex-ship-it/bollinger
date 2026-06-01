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
            if len(closes) < 35: continue

            def calc_band(c):
                """Calculate SMA, upper, lower for a given list of closes (last 20)."""
                s   = sum(c[-20:]) / 20
                sd  = (sum((x-s)**2 for x in c[-20:]) / 20) ** 0.5
                return s, s+2*sd, s-2*sd

            def band_at(closes_all, idx):
                if idx < 20: return None, None, None
                c = closes_all[:idx+1]
                return calc_band(c)

            def ema(prices, period):
                k = 2 / (period + 1)
                e = prices[0]
                for p in prices[1:]:
                    e = p * k + e * (1 - k)
                return e

            def calc_macd(closes_all):
                """Returns (macd_line, signal_line, histogram) for last few days."""
                if len(closes_all) < 35: return [], [], []
                macd_line = []
                for i in range(26, len(closes_all)):
                    fast = ema(closes_all[i-11:i+1], 12)
                    slow = ema(closes_all[i-25:i+1], 26)
                    macd_line.append(fast - slow)
                if len(macd_line) < 9: return macd_line, [], []
                signal = []
                for i in range(8, len(macd_line)):
                    signal.append(ema(macd_line[i-8:i+1], 9))
                hist = [m - s for m, s in zip(macd_line[8:], signal)]
                return macd_line, signal, hist

            # Today's band
            sma, upper, lower = calc_band(closes)
            cur  = closes[-1]
            prev = closes[-2]
            chg  = (cur - prev) / prev * 100
            bw   = (upper - lower) / sma * 100 if sma else 0

            # Yesterday's band (for crossover)
            prev_sma, _, prev_lower = band_at(closes, len(closes)-2) if len(closes) >= 22 else (sma, upper, lower)

            # Crossover flags
            cross_lower = prev < prev_lower and cur >= lower if prev_lower else False
            cross_sma   = prev < prev_sma   and cur >= sma   if prev_sma   else False

            # ── MACD ──
            macd_vals, signal_vals, hist_vals = calc_macd(closes)
            macd_now  = macd_vals[-1]  if len(macd_vals)  >= 2 else 0
            macd_prev = macd_vals[-2]  if len(macd_vals)  >= 2 else 0
            hist_now  = hist_vals[-1]  if len(hist_vals)  >= 2 else 0
            hist_prev = hist_vals[-2]  if len(hist_vals)  >= 2 else 0
            sig_now   = signal_vals[-1] if signal_vals else 0

            # MACD divergence: price makes new low but MACD histogram makes higher low (bullish)
            # Check last 5 days
            price_lower_low = len(closes) >= 2 and closes[-1] < min(closes[-6:-1]) if len(closes) >= 6 else False
            macd_higher_low = len(hist_vals) >= 5 and hist_vals[-1] > min(hist_vals[-5:-1])
            bullish_divergence = price_lower_low and macd_higher_low and hist_now < 0

            # Bearish divergence: price makes new high but MACD histogram makes lower high
            price_higher_high = len(closes) >= 2 and closes[-1] > max(closes[-6:-1]) if len(closes) >= 6 else False
            macd_lower_high   = len(hist_vals) >= 5 and hist_vals[-1] < max(hist_vals[-5:-1])
            bearish_divergence = price_higher_high and macd_lower_high and hist_now > 0

            # MACD cross above signal (bullish crossover)
            macd_cross_up   = macd_prev < signal_vals[-2] and macd_now >= sig_now if len(signal_vals) >= 2 else False
            macd_cross_down = macd_prev > signal_vals[-2] and macd_now <= sig_now if len(signal_vals) >= 2 else False

            # ── Core pattern: Pre-pullback 5-day setup ──
            # Find pullback day (price touched/fell to SMA), verify 5 days before:
            #   - ALL 5 days price > SMA
            #   - >= 3 of 5 days price within near_upper_pct% of upper band
            def check_setup_before_pullback(closes_all, near_upper_pct=5.0, lookback=20):
                n = len(closes_all)
                for pb_ago in range(1, lookback):
                    pb_idx = n - 1 - pb_ago
                    if pb_idx < 25: break
                    s_pb, u_pb, _ = band_at(closes_all, pb_idx)
                    if s_pb is None: break
                    p_pb = closes_all[pb_idx]
                    if p_pb > s_pb * 1.01: continue  # not a pullback day
                    # Check 5 days immediately before the pullback
                    all_above = True
                    near_cnt  = 0
                    for k in range(1, 6):
                        idx_k = pb_idx - k
                        if idx_k < 20: all_above = False; break
                        s_k, u_k, _ = band_at(closes_all, idx_k)
                        if s_k is None: all_above = False; break
                        p_k = closes_all[idx_k]
                        if p_k <= s_k: all_above = False; break
                        if (u_k - p_k) / u_k * 100 <= near_upper_pct:
                            near_cnt += 1
                    if all_above and near_cnt >= 3:
                        return True, pb_ago
                return False, -1

            found_pb5, pb5_ago = check_setup_before_pullback(closes, 5.0)
            found_pb2, pb2_ago = check_setup_before_pullback(closes, 2.0)

            cur_dist_sma = (cur - sma) / sma * 100
            pullback_5pct = found_pb5 and abs(cur_dist_sma) <= 5
            pullback_2pct = found_pb2 and abs(cur_dist_sma) <= 5

            def check_bounce(closes_all, near_upper_pct=5.0, lookback=20):
                if cur <= sma: return False
                found, pb_ago = check_setup_before_pullback(closes_all, near_upper_pct, lookback)
                if not found: return False
                n = len(closes_all)
                pb_idx = n - 1 - pb_ago
                for k in range(1, 4):
                    idx_k = pb_idx + k
                    if idx_k >= n: break
                    s_k, _, _ = band_at(closes_all, idx_k)
                    if s_k and closes_all[idx_k] > s_k:
                        return True
                return False

            bounce_5pct = check_bounce(closes, 5.0)
            bounce_2pct = check_bounce(closes, 2.0)

            def near_upper_consecutive(closes_all, min_days, pct_threshold):
                count = 0
                for d in range(1, min_days + 1):
                    idx = len(closes_all) - d
                    if idx < 20: break
                    s, u, _ = band_at(closes_all, idx)
                    if s is None: break
                    p = closes_all[idx]
                    if p > s and (u - p) / u * 100 <= pct_threshold:
                        count += 1
                    else:
                        break
                return count >= min_days

            near_upper_2pct_3d = near_upper_consecutive(closes, 3, 2.0)
            near_upper_2pct_5d = near_upper_consecutive(closes, 5, 2.0)
            near_upper_5pct_3d = near_upper_consecutive(closes, 3, 5.0)
            near_upper_5pct_5d = near_upper_consecutive(closes, 5, 5.0)

            bounce_3d_2pct = bounce_2pct
            bounce_5d_2pct = bounce_2pct
            bounce_3d_5pct = bounce_5pct
            bounce_5d_5pct = bounce_5pct
            pullback_3d_2pct = pullback_2pct
            pullback_5d_2pct = pullback_2pct
            pullback_3d_5pct = pullback_5pct
            pullback_5d_5pct = pullback_5pct

            results.append({
                "ticker": ticker, "price": round(cur,2),
                "sma": round(sma,2), "upper": round(upper,2), "lower": round(lower,2),
                "bw": round(bw,2), "chg": round(chg,2),
                "crossLower": cross_lower,
                "crossSma":   cross_sma,
                # MACD
                "macd":      round(macd_now, 4),
                "macdSignal":round(sig_now, 4),
                "macdHist":  round(hist_now, 4),
                "macdHistPrev": round(hist_prev, 4),
                "bullishDiv":   bullish_divergence,
                "bearishDiv":   bearish_divergence,
                "macdCrossUp":  macd_cross_up,
                "macdCrossDown":macd_cross_down,
                # Near upper
                "nearUpper2d3": near_upper_2pct_3d,
                "nearUpper2d5": near_upper_2pct_5d,
                "nearUpper5d3": near_upper_5pct_3d,
                "nearUpper5d5": near_upper_5pct_5d,
                # Pullback to SMA (strict 5-day setup before pullback)
                "pullback3d2pct": pullback_3d_2pct,
                "pullback5d2pct": pullback_5d_2pct,
                "pullback3d5pct": pullback_3d_5pct,
                "pullback5d5pct": pullback_5d_5pct,
                # Bounce after pullback
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
