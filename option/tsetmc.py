import requests
import time
from urllib.parse import quote

BASE = "https://cdn.tsetmc.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://tsetmc.com/",
}

session = requests.Session()
session.headers.update(HEADERS)

def get_json(path, retries=3):
    url = BASE + path
    last = None
    for i in range(retries):
        try:
            r = session.get(url, timeout=25)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except Exception as e:
            last = str(e)
        time.sleep(1.5*(i+1))
    raise RuntimeError(f"TSETMC request failed: {url} -> {last}")

def unwrap(obj):
    if isinstance(obj, dict):
        for key in (
            "instrumentOptionMarketWatch", "optionMarketWatch",
            "marketWatch", "marketwatch", "items", "Items"
        ):
            if key in obj and isinstance(obj[key], list):
                return obj[key]
        for v in obj.values():
            if isinstance(v, list):
                return v
    if isinstance(obj, list):
        return obj
    return []

def option_market_watch(flow):
    # This endpoint is documented by community-maintained TSETMC references.
    data = get_json(f"/Instrument/GetInstrumentOptionMarketWatch/{flow}")
    return unwrap(data)

def search_instrument(symbol):
    data = get_json("/Instrument/GetInstrumentSearch/" + quote(symbol, safe=""))
    if isinstance(data, dict):
        for k in ("instrumentSearch", "items", "Items"):
            if isinstance(data.get(k), list):
                return data[k]
    return data if isinstance(data, list) else []

def closing_info(inscode):
    data = get_json(f"/ClosingPrice/GetClosingPriceInfo/{inscode}")
    if isinstance(data, dict):
        return data.get("closingPriceInfo", data)
    return data

def daily_prices(inscode, top=60):
    data = get_json(f"/ClosingPrice/GetClosingPriceDailyList/{inscode}/{top}")
    if isinstance(data, dict):
        rows = data.get("closingPriceDaily", [])
    else:
        rows = data
    if not isinstance(rows, list):
        return []
    prices = []
    for row in rows:
        if isinstance(row, dict):
            for k in ("pClosing","pDrCotVal","pc","pl","close","closingPrice"):
                if row.get(k) not in (None, 0, "0"):
                    try:
                        prices.append(float(row[k]))
                        break
                    except Exception:
                        pass
    return prices

def val(row, names, default=None):
    if not isinstance(row, dict):
        return default
    # exact names first
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    # case-insensitive fallback
    lower = {str(k).lower(): v for k,v in row.items()}
    for n in names:
        if n.lower() in lower and lower[n.lower()] not in (None, ""):
            return lower[n.lower()]
    return default

def normalize_option(row):
    # Field names vary slightly across TSETMC mirrors/releases.
    symbol = val(row, ["lVal18AFC","symbol","symbolName","namad","namadNam"])
    name = val(row, ["lVal30","name","fullName"])
    inscode = val(row, ["insCode","inscode","instrumentId"])

    kind_raw = str(val(row, [
        "type","optionType","optionTypeName","noe","noeNam",
        "instrumentType","typeName"
    ], "")).lower()
    kind = "put" if any(x in kind_raw for x in ["put","فروش","putoption","2"]) else "call"

    # Some responses expose the type as a numeric field; if absent, infer from symbol prefix.
    if "ض" in str(symbol or ""):
        # Iranian option symbols conventionally use ط/ض in prefixes; fallback below.
        pass
    if "ط" in str(symbol or ""):
        kind = "put"

    strike = val(row, [
        "qeymateEmal","qeymatEmal","strikePrice","strike",
        "exercisePrice","exercise"
    ])
    underlying = val(row, [
        "qeymateMabna","qeymatMabna","underlyingPrice",
        "basePrice","priceBase","mabnaPrice"
    ])
    underlying_symbol = val(row, [
        "baseSymbol","underlyingSymbol","mabnaSymbol","symbolMabna",
        "namadMabna","lVal18AFCBase"
    ])
    last = val(row, [
        "pDrCotVal","lastPrice","last","lastTradedPrice","price",
        "pClosing","pc","closingPrice"
    ])
    close = val(row, ["pClosing","closingPrice","pc","close"])
    volume = val(row, ["qTotTran5J","volume","qTotTran","totalVolume"])
    trades = val(row, ["zTotTran","tradeCount","numberOfTrades","count"])
    days = val(row, [
        "baghimandeTaSarresid","remainingDays","daysToMaturity",
        "daysRemaining","daysToExpiry"
    ])
    expiry = val(row, ["tarixSarresid","expiryDate","expirationDate","sarresid"])

    def num(x):
        try:
            return float(str(x).replace(",", ""))
        except Exception:
            return None

    def integer(x):
        try:
            return int(float(str(x).replace(",", "")))
        except Exception:
            return None

    return {
        "symbol": symbol,
        "name": name,
        "inscode": inscode,
        "kind": kind,
        "strike": num(strike),
        "underlying": num(underlying),
        "underlying_symbol": underlying_symbol,
        "last": num(last),
        "close": num(close),
        "volume": integer(volume),
        "trades": integer(trades),
        "days": integer(days),
        "expiry": expiry,
        "raw": row,
    }
