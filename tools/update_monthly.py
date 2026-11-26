#!/usr/bin/env python3
"""統合幕僚監部「月間緊急発進状況」の本文テキスト（pdftotext -layout の出力）から回数を読み取り、
検算（方面隊の合計・国地域の合計・各行の合計列）がすべて合ったときだけ tools/m2026.json を書き換える。
使い方: python3 tools/update_monthly.py data/js_scramble/p20261113_06.txt https://www.mod.go.jp/js/pdf/2026/p20261113_06.pdf"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "tools", "m2026.json")
FY = 2026
Z2H = str.maketrans("０１２３４５６７８９－（）", "0123456789-()")

def parse(text):
    t = text.translate(Z2H)
    fy = re.search(r"(\d{4})年度における緊急発進実施状況", t)
    asof = re.search(r"\((\d{4})年(\d{1,2})月(\d{1,2})日現在\)", t)
    if not fy or not asof:
        raise ValueError("年度または現在日が見つからない")
    lines = t.split("\n")
    def row(label, start=0):
        for i in range(start, len(lines)):
            if re.match(r"\s*" + label + r"\s", lines[i].replace("合 計", "合計")):
                vals = re.findall(r"(\d+|-)回", lines[i])
                if len(vals) == 13:
                    return i, vals
        raise ValueError(f"行が見つからない: {label}")
    def nums(vals):
        months = []
        for v in vals[:12]:
            if v == "-": break
            months.append(int(v))
        return months, int(vals[12])
    out, totals = {}, {}
    i, v = row("回数"); out["合計"], totals["合計"] = nums(v)
    hi = next(k for k, l in enumerate(lines) if "航空方面隊別" in l)
    ci = next(k for k, l in enumerate(lines) if "国・地域別" in l)
    for k in ["北空", "中空", "西空", "南西空"]:
        _, v = row(k, hi); out[k], totals[k] = nums(v)
    _, v = row("合計", hi); hsum, htot = nums(v)
    countries = []
    for l in lines[ci + 1:]:
        m = re.match(r"\s*(\S+?)\s+(?:\d+|-)回", l.replace("合 計", "合計"))
        if not m: continue
        name = m.group(1)
        if name == "合計": break
        _, v = row(re.escape(name), ci); out[name], totals[name] = nums(v); countries.append(name)
    n = len(out["合計"])
    # 検算
    for k, ms in out.items():
        if len(ms) != n: raise ValueError(f"月数が合わない: {k}")
        if sum(ms) != totals[k]: raise ValueError(f"合計列が合わない: {k} {sum(ms)} != {totals[k]}")
    for i in range(n):
        h = sum(out[k][i] for k in ["北空", "中空", "西空", "南西空"])
        c = sum(out[k][i] for k in countries)
        if not (h == out["合計"][i] == c == hsum[i]):
            raise ValueError(f"{i + 4 if i < 9 else i - 8}月の内訳が合わない: 方面隊{h} 国{c} 合計{out['合計'][i]}")
    order = ["合計", "北空", "中空", "西空", "南西空", "中国", "ロシア"]
    months = {k: out[k] for k in order if k in out}
    months.update({k: out[k] for k in countries if k not in months})
    return int(fy.group(1)), f"{asof.group(1)}-{int(asof.group(2)):02d}-{int(asof.group(3)):02d}", months

def apply(txt_path, url):
    """戻り値: 'updated' / 'same' / 'older' / 'newfy:<年度>'。読み取りや検算に失敗したら例外。"""
    fy, asof, months = parse(open(txt_path, encoding="utf-8").read())
    if fy != FY:
        return f"newfy:{fy}"
    cur = json.load(open(JS, encoding="utf-8"))
    if asof < cur["asof"]:
        return "older"
    m = re.search(r"p(\d{4})(\d{2})(\d{2})_", url)
    pub = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else cur["published"]
    y, mo, d = (int(x) for x in asof.split("-"))
    new = {"fy": fy, "asof": asof, "published": pub,
           "source_title": f"統合幕僚監部「月間緊急発進状況（{y}年{mo}月{d}日現在）」", "source_url": url, "months": months}
    if new == cur:
        return "same"
    tmp = JS + ".tmp"
    json.dump(new, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, JS)
    return "updated"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(parse(open(sys.argv[1], encoding="utf-8").read()))
    else:
        print(apply(sys.argv[1], sys.argv[2]))
