import datetime as dt
import jdatetime

from config import *
from option_pricing import bs_price, historical_vol, intrinsic
from tsetmc import option_market_watch, normalize_option, search_instrument, daily_prices

def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def resolve_underlying(opt):
    # Prefer the value supplied by the option market-watch.
    if opt.get("underlying") and opt["underlying"] > 0:
        return opt["underlying"], opt.get("underlying_symbol"), None

    sym = opt.get("underlying_symbol")
    if not sym:
        return None, None, None

    results = search_instrument(sym)
    if not results:
        return None, sym, None

    best = results[0]
    ins = best.get("insCode") or best.get("inscode")
    symbol = best.get("lVal18AFC") or best.get("symbol") or sym

    price = None
    # Search result sometimes includes current price.
    for k in ("pDrCotVal","pClosing","pc","price","last"):
        if best.get(k) not in (None, 0):
            try:
                price = float(best[k])
                break
            except Exception:
                pass

    return price, symbol, ins

def scan():
    rows = []
    raw = []
    for flow in (1, 2):
        try:
            raw.extend(option_market_watch(flow))
        except Exception as e:
            print("option endpoint error", flow, e)

    seen = set()
    for item in raw:
        o = normalize_option(item)
        if not o["symbol"] or o["symbol"] in seen:
            continue
        seen.add(o["symbol"])

        if not o["last"] or o["last"] <= 0:
            continue
        if o["days"] is not None and (o["days"] <= 0 or o["days"] > MAX_DAYS):
            continue
        if o["trades"] is not None and o["trades"] < MIN_TRADES:
            continue
        if o["volume"] is not None and o["volume"] < MIN_VOLUME:
            continue
        if not o["strike"]:
            continue

        S = o["underlying"]
        base_symbol = o["underlying_symbol"]
        base_ins = None

        if not S or S <= 0:
            S, base_symbol, base_ins = resolve_underlying(o)
        if not S or S <= 0:
            continue

        K = o["strike"]
        T = max((o["days"] or 1) / 365.0, 1/365.0)

        iv = None
        if base_ins:
            try:
                prices = daily_prices(base_ins, HIST_VOL_DAYS)
                iv = historical_vol(prices)
            except Exception:
                pass

        if iv is None:
            # If no history could be fetched, use a neutral configurable fallback.
            iv = 0.45
        iv = min(max(iv, MIN_VOL), MAX_VOL)

        intr = intrinsic(S, K, o["kind"])
        fair = bs_price(S, K, T, RISK_FREE_RATE, iv, DIVIDEND_YIELD, o["kind"])

        market = o["last"]
        discount_intr = (intr-market)/intr if intr > 0 else None
        discount_model = (fair-market)/fair if fair and fair > 0 else None

        o.update({
            "base_price": S,
            "base_symbol": base_symbol,
            "iv": iv,
            "intrinsic": intr,
            "fair": fair,
            "discount_intrinsic": discount_intr,
            "discount_model": discount_model,
            "time_value": market-intr,
        })
        rows.append(o)

    # First show the contracts with the largest discount to model value.
    rows.sort(key=lambda x: (x["discount_model"] if x["discount_model"] is not None else -999), reverse=True)
    return rows

if __name__ == "__main__":
    import json
    print(json.dumps(scan()[:20], ensure_ascii=False, indent=2))
