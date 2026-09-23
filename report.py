from datetime import datetime
from pathlib import Path
import html

from config import TITLE, SUBTITLE, MIN_DISCOUNT

def fmt(x, digits=0):
    if x is None:
        return "-"
    if digits == 0:
        return f"{x:,.0f}"
    return f"{x:,.{digits}f}"

def pct(x):
    return "-" if x is None else f"{x*100:.1f}%"

def build(rows, out="docs/index.html", error=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    good = [r for r in rows if r.get("discount_model") is not None and r["discount_model"] >= MIN_DISCOUNT]
    good.sort(key=lambda r: r["discount_model"], reverse=True)

    cards = []
    for r in good:
        cls = "good"
        cards.append(f"""
        <article class="card {cls}">
          <div class="top">
            <b>{html.escape(str(r['symbol']))}</b>
            <span class="badge">{'Call' if r['kind']=='call' else 'Put'}</span>
          </div>
          <div class="sub">{html.escape(str(r.get('base_symbol') or '-'))}</div>
          <div class="grid">
            <span>قیمت بازار</span><strong>{fmt(r['last'])}</strong>
            <span>ارزش مدل</span><strong>{fmt(r['fair'])}</strong>
            <span>ارزش ذاتی</span><strong>{fmt(r['intrinsic'])}</strong>
            <span>فاصله از مدل</span><strong class="green">{pct(r['discount_model'])}</strong>
            <span>قیمت پایه</span><strong>{fmt(r['base_price'])}</strong>
            <span>اعمال</span><strong>{fmt(r['strike'])}</strong>
            <span>روز مانده</span><strong>{r.get('days') or '-'}</strong>
            <span>نوسان سالانه</span><strong>{pct(r.get('iv'))}</strong>
          </div>
          <details>
            <summary>جزئیات</summary>
            <div class="details">
              ارزش زمانی بازار: {fmt(r.get('time_value'))}<br>
              زیر ارزش ذاتی: {pct(r.get('discount_intrinsic'))}<br>
              حجم: {fmt(r.get('volume'))}<br>
              تعداد معاملات: {fmt(r.get('trades'))}<br>
              سررسید: {html.escape(str(r.get('expiry') or '-'))}
            </div>
          </details>
        </article>
        """)

    body = "\n".join(cards) if cards else """
      <div class="empty">
        در اجرای فعلی قرارداد واجد شرایط پیدا نشد.
        اگر داده TSETMC در دسترس نباشد، وضعیت خطا را پایین صفحه ببین.
      </div>
    """

    err = f'<div class="error">خطا: {html.escape(error)}</div>' if error else ""

    page = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache">
<title>{TITLE}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#f4f6f8;font-family:Tahoma,Arial,sans-serif;color:#18212b}}
.wrap{{max-width:900px;margin:auto;padding:16px}}
header{{background:#17212b;color:white;border-radius:18px;padding:20px;margin-bottom:14px}}
h1{{font-size:22px;margin:0 0 7px}} .muted{{opacity:.75;font-size:12px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}}
.stat{{background:white;border-radius:14px;padding:12px 16px;box-shadow:0 2px 10px #0000000d}}
.card{{background:white;border-radius:18px;padding:17px;margin:12px 0;box-shadow:0 3px 14px #00000010;border-right:5px solid #20a05a}}
.top{{display:flex;justify-content:space-between;align-items:center;font-size:18px}}
.badge{{font-size:11px;background:#eef2f6;border-radius:20px;padding:5px 9px}}
.sub{{color:#687583;margin:6px 0 12px;font-size:13px}}
.grid{{display:grid;grid-template-columns:1fr auto;gap:8px 16px;font-size:13px}}
.grid strong{{text-align:left}}
.green{{color:#138a48}}
details{{margin-top:14px}} summary{{cursor:pointer;color:#315b7d;font-size:13px}}
.details{{padding-top:9px;line-height:2;font-size:12px;color:#59636d}}
.empty,.error{{background:white;border-radius:16px;padding:20px;margin-top:15px}}
.error{{color:#9b2226;border-right:4px solid #c33}}
footer{{font-size:11px;color:#77818c;text-align:center;padding:20px}}
@media(max-width:520px){{.wrap{{padding:10px}} header{{border-radius:14px}}}}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>🔎 {TITLE}</h1>
<div>{SUBTITLE}</div>
<div class="muted">آخرین بروزرسانی: {now}</div>
</header>
<div class="stats">
<div class="stat">🟢 فرصت‌ها: <b>{len(good)}</b></div>
<div class="stat">کل قراردادهای بررسی‌شده: <b>{len(rows)}</b></div>
<div class="stat">حداقل فاصله: <b>{MIN_DISCOUNT*100:.0f}%</b></div>
</div>
{err}
{body}
<footer>
این صفحه ابزار محاسباتی است؛ ارزش مدل به نوسان، نرخ بدون ریسک و فرضیات وابسته است و «ارزش ذاتی» با «ارزش منصفانه» یکسان نیست.
</footer>
</div>
</body>
</html>"""

    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page, encoding="utf-8")
    return str(p)
