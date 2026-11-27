#!/usr/bin/env python3
"""スクランブル.com の静的サイト生成。
tools/content/<name>.html → /<name>/（__ は / に。index は トップ）。
1行目 title、2行目 description、3行目以降 本文（h1・p.updated・本文・section.sources）。
本文中の {{...}} は data.py の公式数字から表やグラフを差し込む。"""
import glob, html, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import YEARS, COUNTRY, MONTHS, M2025, M2026, M2026_ASOF, M2026_ASOF_DATE, SOURCES, NAHA_LIVES, CHANNEL_URL, CHANNEL_LIVE
from data import KOMATSU_RUNWAY, KOMATSU_SCRAMBLE_MILESTONE, KOMATSU_FIRST_F35A, KOMATSU_PASSENGERS_2024, TERRITORIAL_SEA_NM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://xn--pckta2g7cl0c.com"
SITE = "スクランブル.com"
CSS_VER = "20261127i"
AD = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1061443138303693" crossorigin="anonymous"></script>'
NAV = [("那覇のスクランブル", "/naha/"), ("最新の回数", "/latest/"), ("年度別の推移", "/data/"), ("国・地域別", "/country/"), ("方面隊別", "/houmentai/"), ("スクランブルとは", "/shikumi/")]
esc = html.escape

def strip(s):
    return re.sub(r"<[^>]+>", "", s).strip()

def bars(pairs, unit="回", hi=None):
    m = max(v for _, v in pairs) or 1
    rows = []
    for label, v in pairs:
        w = round(v / m * 100, 1)
        cls = ' class="hi"' if hi and label == hi else ""
        rows.append(f'<div class="bar-row"><span class="bl">{esc(label)}</span><span class="bt"><span{cls} style="width:{w}%"></span></span><span class="bv">{v:,}{unit}</span></div>')
    return '<div class="bars">' + "".join(rows) + "</div>"

def table(head, rows):
    h = "".join(f"<th>{esc(x)}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{x if isinstance(x, str) else f'{x:,}'}</td>" for x in r) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table><tr>{h}</tr>{b}</table></div>'

def pct(a, b):
    return f"{a / b * 100:.0f}%"

def naha_live():
    vid, day, note = NAHA_LIVES[0]
    player = (f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{esc(note)}" loading="lazy" '
              f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>')
    cards = "".join(f'<a class="ytc" href="https://www.youtube.com/watch?v={v}" target="_blank" rel="noopener">'
                    f'<img src="https://img.youtube.com/vi/{v}/hqdefault.jpg" alt="{esc(n)}" loading="lazy">'
                    f'<span><b>{esc(d)}</b>{esc(n)}</span></a>' for v, d, n in NAHA_LIVES)
    btns = (f'<p class="ytbtns"><a href="{CHANNEL_LIVE}" target="_blank" rel="noopener">ちんあなごチャンネルのライブ配信一覧</a>'
            f'<a href="{CHANNEL_URL}" target="_blank" rel="noopener">チャンネルを見る</a></p>')
    return f'<div class="live-box">{player}<div class="ytcards">{cards}</div>{btns}</div>'

def fill(body):
    last = max(YEARS)
    rep = {
        "YEAR_BARS": lambda: bars([(f"{y}年度", v[0]) for y, v in YEARS.items()], hi="2016年度"),
        "YEAR_TABLE": lambda: table(["年度", "合計", "北部航空方面隊", "中部航空方面隊", "西部航空方面隊", "南西航空方面隊"],
                                    [[f"{y}年度", *v] for y, v in sorted(YEARS.items(), reverse=True)]),
        "COUNTRY_TABLE": lambda: table(["年度", "中国", "ロシア", "台湾", "北朝鮮", "その他", "合計"],
                                       [[f"{y}年度", *v, sum(v)] for y, v in sorted(COUNTRY.items(), reverse=True)]),
        "COUNTRY_SHARE": lambda: table(["年度", "中国機の割合", "ロシア機の割合"],
                                       [[f"{y}年度", pct(v[0], sum(v)), pct(v[1], sum(v))] for y, v in sorted(COUNTRY.items(), reverse=True)]),
        "M2026_BARS": lambda: bars(list(zip(MONTHS, M2026["合計"]))),
        "M2026_TABLE": lambda: table(["区分", *MONTHS[:len(M2026["合計"])], "計"],
                                     [[k, *v, sum(v)] for k, v in M2026.items() if k == "合計" or any(v)]),
        "M2025_TABLE": lambda: table(["区分", *MONTHS, "計"], [[k, *v, sum(v)] for k, v in M2025.items()]),
        "M2025_BARS": lambda: bars(list(zip(MONTHS, M2025["合計"]))),
        "HOUMEN_2026": lambda: bars([("北部航空方面隊", sum(M2026["北空"])), ("中部航空方面隊", sum(M2026["中空"])),
                                     ("西部航空方面隊", sum(M2026["西空"])), ("南西航空方面隊", sum(M2026["南西空"]))]),
        "HOUMEN_2025": lambda: bars([("北部航空方面隊", YEARS[last][1]), ("中部航空方面隊", YEARS[last][2]),
                                     ("西部航空方面隊", YEARS[last][3]), ("南西航空方面隊", YEARS[last][4])]),
        "CMP_MONTH": lambda: table(["月", "2025年度", "2026年度", "差"],
                                   [[m, a, b, f"{b - a:+d}"] for m, a, b in zip(MONTHS, M2025["合計"], M2026["合計"])]),
        "CMP_COUNTRY": lambda: table(["月", "中国 2025", "中国 2026", "ロシア 2025", "ロシア 2026"],
                                     [[m, a, b, c, d] for m, a, b, c, d in zip(MONTHS, M2025["中国"], M2026["中国"], M2025["ロシア"], M2026["ロシア"])]),
        "HOUMEN_SHARE": lambda: table(["年度", "北空", "中空", "西空", "南西空"],
                                      [[f"{y}年度", *[pct(x, v[0]) for x in v[1:]]] for y, v in sorted(YEARS.items(), reverse=True)]),
        "NAHA_TOTAL": lambda: f"{sum(M2026['南西空']):,}",
        "NAHA_PCT": lambda: pct(sum(M2026["南西空"]), sum(M2026["合計"])),
        "NAHA_YEAR_BARS": lambda: bars([(f"{y}年度", v[4]) for y, v in YEARS.items()], hi="2016年度"),
        "NAHA_YEAR_TABLE": lambda: table(["年度", "全国の合計", "南西航空方面隊", "全国に占める割合"],
                                         [[f"{y}年度", v[0], v[4], pct(v[4], v[0])] for y, v in sorted(YEARS.items(), reverse=True)]),
        "NAHA_M2026_BARS": lambda: bars(list(zip(MONTHS, M2026["南西空"]))),
        "NAHA_M2025_BARS": lambda: bars(list(zip(MONTHS, M2025["南西空"]))),
        "NAHA_CMP": lambda: table(["月", "2025年度", "2026年度", "差"],
                                  [[m, a, b, f"{b - a:+d}"] for m, a, b in zip(MONTHS, M2025["南西空"], M2026["南西空"])]),
        "NAHA_LIVE": lambda: naha_live(),
        "YEAR_DIFF": lambda: table(["年度", "合計", "前年度からの増減"],
                                   [[f"{y}年度", v[0], (f"{v[0] - YEARS[y - 1][0]:+,d}" if y - 1 in YEARS else "―")] for y, v in sorted(YEARS.items(), reverse=True)]),
        "HOUMEN_MAXMIN": lambda: table(["方面隊", "多かった年度", "少なかった年度"],
                                       [[n, f"{max(YEARS, key=lambda y: YEARS[y][i])}年度（{max(v[i] for v in YEARS.values()):,}回）",
                                         f"{min(YEARS, key=lambda y: YEARS[y][i])}年度（{min(v[i] for v in YEARS.values()):,}回）"]
                                        for i, n in [(1, "北部航空方面隊"), (2, "中部航空方面隊"), (3, "西部航空方面隊"), (4, "南西航空方面隊")]]),
        "PACE_TABLE": lambda: table(["区分", "2026年度（4月〜10月）", "2025年度の同じ時期", "2025年度の1年間"],
                                    [[k, sum(M2026[k]), sum(M2025[k][:len(M2026[k])]), sum(M2025[k])] for k in ["合計", "北空", "中空", "西空", "南西空", "中国", "ロシア"]]),
        "LATEST_TOTAL": lambda: f"{sum(M2026['合計']):,}",
        "LATEST_ASOF": lambda: M2026_ASOF,
        "KOMATSU_RUNWAY": lambda: "×".join(f"{size:,}m" for size in KOMATSU_RUNWAY),
        "KOMATSU_SCRAMBLE_MILESTONE": lambda: f"{KOMATSU_SCRAMBLE_MILESTONE:,}",
        "KOMATSU_FIRST_F35A": lambda: f"{KOMATSU_FIRST_F35A:,}",
        "KOMATSU_DOMESTIC_2024": lambda: f"{KOMATSU_PASSENGERS_2024[0]:,}",
        "KOMATSU_INTERNATIONAL_2024": lambda: f"{KOMATSU_PASSENGERS_2024[1]:,}",
        "TERRITORIAL_SEA_NM": lambda: str(TERRITORIAL_SEA_NM),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: rep[m.group(1)](), body)

def src_links(body):
    # <li data-src="key"></li> を公式資料へのリンクにする
    return re.sub(r'<li data-src="(\w+)"></li>', lambda m: f'<li><a href="{SOURCES[m.group(1)][1]}" rel="noopener" target="_blank">{esc(SOURCES[m.group(1)][0])}</a></li>', body)

def blockify(body):
    # h2 ごとに白い箱（section.block）に入れる
    parts = re.split(r"(?=<h2[ >])", body)
    out = []
    for p in parts:
        if not p.strip(): continue
        if p.lstrip().startswith("<h2"): out.append(f'<section class="block">{p}</section>\n')
        else: out.append(p)
    return "".join(out)

def url_of(f):
    n = os.path.basename(f)[:-5]
    return "/" if n == "index" else "/" + n.replace("__", "/") + "/"


# ---- 本文中の {{=式}} を、最新の月間データから計算した文字に置き換える（毎月の自動更新で文章も追随させる）
def expr_ctx():
    n = len(M2026["合計"]); L = MONTHS[n - 1]
    y_, m_, d_ = (int(x) for x in M2026_ASOF_DATE.split("-"))
    cur = lambda k: M2026.get(k, [0] * n)
    s = lambda k: sum(cur(k))
    p = lambda k: sum(M2025[k][:n])
    y = lambda k: sum(M2025[k])
    mv = lambda k, mon: cur(k)[MONTHS.index(mon)]
    pv = lambda k, mon: M2025[k][MONTHS.index(mon)]
    c = lambda x: f"{x:,}"
    def top(k):
        v = cur(k); return MONTHS[v.index(max(v))]
    def topv(k): return max(cur(k))
    def tops(k, num=3):
        v = cur(k); idx = sorted(range(n), key=lambda i: -v[i])[:num]
        return "、".join(f"{MONTHS[i]}（{v[i]}回）" for i in sorted(idx))
    def mlist(k):
        return "、".join(f"{MONTHS[i]}{v}回" for i, v in enumerate(cur(k)))
    H = ["北空", "中空", "西空", "南西空"]
    HN = {"北空": "北部航空方面隊", "中空": "中部航空方面隊", "西空": "西部航空方面隊", "南西空": "南西航空方面隊"}
    def nsw_top():
        exc = [i for i in range(n) if cur("南西空")[i] < max(cur(h)[i] for h in H)]
        if not exc: return "すべての月で4つの航空方面隊のなかでもっとも多く"
        if len(exc) == n: return "4つの航空方面隊のなかで月ごとの最多にはなっていないものの"
        return "・".join(MONTHS[i] for i in exc) + "を除くすべての月で4つの航空方面隊のなかでもっとも多く"
    def nsw_exc():
        out = []
        for i in range(n):
            mx = max(H, key=lambda h: cur(h)[i])
            if mx != "南西空": out.append(f"{MONTHS[i]}は{HN[mx]}（{cur(mx)[i]}回）が南西航空方面隊（{cur('南西空')[i]}回）を上回りました")
        return ("。".join(out) + "。") if out else "どの月も南西航空方面隊が最多でした。"
    def vs_year(k):
        a, b = s(k), y(k)
        return f"2025年度の1年間（{c(b)}回）をすでに上回りました" if a > b else (f"2025年度の1年間（{c(b)}回）と同じ回数になりました" if a == b else f"2025年度の1年間（{c(b)}回）まであと{c(b - a)}回です")
    def ratio(k):
        a, b = s(k), y(k); r = a / b
        return f"約{r:.1f}倍" if r >= 1.15 else ("ほぼ同じ" if r >= 0.9 else f"約{round(r * 10)}割")
    def diffw(a, b):
        return f"{c(a - b)}回多く" if a > b else (f"{c(b - a)}回少なく" if a < b else "同じ回数に")
    def mcmp(k):
        up = [MONTHS[i] for i in range(n) if cur(k)[i] > M2025[k][i]]
        dn = [MONTHS[i] for i in range(n) if cur(k)[i] < M2025[k][i]]
        return up, dn
    def cmp_sentence(k="合計"):
        up, dn = mcmp(k)
        if not dn: return "すべての月で2025年度を上回っています"
        if not up: return "すべての月で2025年度を下回っています"
        if len(dn) <= len(up): return f"{'・'.join(dn)}を除くすべての月で2025年度を上回っています"
        return f"{'・'.join(up)}は2025年度を上回り、{'・'.join(dn)}は下回っています"
    def bigdiff(k="合計"):
        d = [cur(k)[i] - M2025[k][i] for i in range(n)]; i = d.index(max(d))
        return f"{MONTHS[i]}で、2025年度の{M2025[k][i]}回に対して2026年度は{cur(k)[i]}回（{d[i]}回多い）"
    import datetime as _dt
    days = (_dt.date(y_, m_, d_) - _dt.date(2026, 4, 1)).days + 1
    import calendar as _cal
    ldays = _cal.monthrange(y_, m_)[1]
    nk_zero = all(v == 0 for v in cur("北朝鮮"))
    nxt = MONTHS[n] if n < 12 else None
    pub = MONTHS[(n + 1) % 12] if n < 12 else "4月"
    return dict(n=n, L=L, R=f"4月〜{L}", NM=f"{n}か月", AD=f"{y_}年{m_}月{d_}日", ADM=f"{y_}年{m_}月", s=s, p=p, y=y, mv=mv, pv=pv,
                c=c, top=top, topv=topv, tops=tops, mlist=mlist, nsw_top=nsw_top, nsw_exc=nsw_exc, vs_year=vs_year, ratio=ratio,
                diffw=diffw, cmp_sentence=cmp_sentence, bigdiff=bigdiff, days=days, ldays=ldays, nk_zero=nk_zero, nxt=nxt, pub=pub,
                pct=lambda a, b: f"{a / b * 100:.0f}%", MONTHS=MONTHS, M2026=M2026)

def exprs(text):
    ctx = expr_ctx()
    return re.sub(r"\{\{=(.+?)\}\}", lambda m: str(eval(m.group(1), dict(ctx))), text)

def picked_rows():
    # seo-system の gh-grow が Wikimedia Commons から選んだ写真（slug・画像・元のページ・撮影者・ライセンス・説明）。写真の取り込みの Actions はこの表を書き換えない
    rows = {}
    p = os.path.join(ROOT, "tools", "photos", "picked.tsv")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8").read().splitlines()[1:]:
            c = l.split("\t")
            if len(c) >= 7 and c[1].startswith("https://"): rows.setdefault(c[0], []).append(c)
    return rows

def photo_hero(url, h1, updated):
    ph = picked_rows().get(url)
    if not ph: return ""
    c = [html.escape(x) for x in ph[0]]
    credit = (f'<p class="credit">写真：{c[6]} {c[3]} / <a href="{c[5]}" rel="noopener license" target="_blank">{c[4]}</a>'
              f'（<a href="{c[2]}" rel="noopener" target="_blank">Wikimedia Commons</a>）</p>')
    return (f'<div class="page-hero photo-hero" style="background-image:linear-gradient(180deg,rgba(6,22,44,.35),rgba(6,22,44,.88)),url({c[1]})">'
            f'<h1>{h1}</h1>{updated}{credit}</div>\n')

def link_cards(main):
    # リンクが3つ以上ならぶ一覧は、写真つきのカードにする
    photos = picked_rows()
    def rep(m):
        items = re.findall(r'<li><a href="([^"]+)">(.*?)</a>(?:：|・)?(.*?)</li>', m.group(0), re.S)
        if len(items) < 3: return m.group(0)
        out = []
        for u, t, d in items:
            ph = photos.get(u)
            img = f'<img class="thumb" src="{html.escape(ph[0][1])}" alt="{html.escape(ph[0][6])}" loading="lazy">' if ph else ""
            out.append(f'<a class="card{" has-thumb" if img else ""}" href="{u}">{img}<strong>{strip(t)}</strong><small>{strip(d)}</small></a>')
        return '<div class="cards">' + "".join(out) + "</div>"
    return re.sub(r"<ul>(?:\s*<li><a href=(?:(?!</li>).)*</li>)+\s*</ul>", rep, main, flags=re.S)

def render(url, title, desc, body):
    body = src_links(fill(body))
    m = re.search(r"<h1>(.*?)</h1>\s*(<p class=\"updated\">.*?</p>)?", body, re.S)
    hero = ""
    if m:
        body = body[:m.start()] + body[m.end():]
        hero = photo_hero(url, m.group(1), m.group(2) or "") or f'<div class="page-hero"><h1>{m.group(1)}</h1>{m.group(2) or ""}</div>\n'
    k = body.find('<section class="sources">')
    main_part, src = (body[:k], body[k:].replace('<section class="sources">', '<section class="sources block">')) if k >= 0 else (body, "")
    crumb = "" if url == "/" else f'<div class="crumb"><a href="/">{SITE}</a> › {esc(strip(m.group(1)) if m else title)}</div>\n'
    nav = "".join(f'<a href="{u}">{t}</a>' for t, u in NAV)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{DOMAIN}{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{'website' if url == '/' else 'article'}">
<meta property="og:url" content="{DOMAIN}{url}">
<link rel="stylesheet" href="/assets/style.css?v={CSS_VER}">
{AD}
</head>
<body>
<header class="site"><div class="wrap">
  <a class="logo" href="/">スクランブル<span>.com</span></a>
  <nav class="global">{nav}</nav>
</div></header>

<main><div class="wrap">
{crumb}{hero}{blockify(link_cards(main_part))}{src}
</div></main>

<footer class="site"><div class="wrap">
  <p>{SITE} は、航空自衛隊の緊急発進（スクランブル）について、防衛省・統合幕僚監部の公式発表の数字をまとめた情報サイトです。防衛省・自衛隊とは関係のない、ちんあなご編集部のサイトです。</p>
  <p>{" ・ ".join(f'<a href="{u}">{t}</a>' for t, u in [("トップ", "/")] + NAV)}</p>
  <p><a href="/operator/">運営者情報</a> ・ <a href="/editorial-policy/">編集方針</a> ・ <a href="/contact/">お問い合わせ</a> ・ <a href="/privacy/">プライバシーポリシー</a> ・ <a href="/disclaimer/">免責事項</a></p>
  <p>© 2026 {SITE}</p>
</div></footer>
</body>
</html>
"""

def main():
    urls = []
    for f in sorted(glob.glob(os.path.join(ROOT, "tools", "content", "*.html"))):
        lines = exprs(open(f, encoding="utf-8").read()).split("\n", 2)
        if len(lines) < 3 or '<section class="sources">' not in lines[2]: continue
        url = url_of(f)
        out = os.path.join(ROOT, url.strip("/"), "index.html") if url != "/" else os.path.join(ROOT, "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        dm = re.search(r'content="([^"]*)"', lines[1])
        open(out, "w", encoding="utf-8").write(render(url, html.unescape(strip(lines[0])), html.unescape(dm.group(1)) if dm else strip(lines[1]), lines[2]))
        urls.append(url)
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    print("pages", len(urls))

if __name__ == "__main__":
    main()
