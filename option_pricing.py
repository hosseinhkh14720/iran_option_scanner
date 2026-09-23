import math

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_price(S, K, T, r, sigma, q=0.0, kind="call"):
    if S <= 0 or K <= 0:
        return None
    if T <= 0:
        if kind == "call":
            return max(S-K, 0.0)
        return max(K-S, 0.0)
    if sigma <= 0:
        if kind == "call":
            return max(S*math.exp(-q*T) - K*math.exp(-r*T), 0.0)
        return max(K*math.exp(-r*T) - S*math.exp(-q*T), 0.0)

    st = sigma * math.sqrt(T)
    d1 = (math.log(S/K) + (r-q+0.5*sigma*sigma)*T) / st
    d2 = d1 - st

    if kind == "call":
        return S*math.exp(-q*T)*norm_cdf(d1) - K*math.exp(-r*T)*norm_cdf(d2)
    return K*math.exp(-r*T)*norm_cdf(-d2) - S*math.exp(-q*T)*norm_cdf(-d1)

def historical_vol(prices):
    # annualized log-return volatility
    vals = [float(x) for x in prices if x is not None and float(x) > 0]
    if len(vals) < 10:
        return None
    rets = []
    for a,b in zip(vals[:-1], vals[1:]):
        if a > 0 and b > 0:
            rets.append(math.log(b/a))
    if len(rets) < 8:
        return None
    mean = sum(rets)/len(rets)
    var = sum((x-mean)**2 for x in rets)/(len(rets)-1)
    return math.sqrt(var*252)

def intrinsic(S, K, kind):
    return max(S-K, 0.0) if kind == "call" else max(K-S, 0.0)
