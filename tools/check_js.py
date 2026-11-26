#!/usr/bin/env python3
"""統合幕僚監部の報道発表資料一覧から、題名に「緊急発進」が入ったPDFを探す（GitHub Actions で実行）。
新しいPDFが見つかったら、本文テキストを data/js_scramble/<ファイル名>.txt に保存し、
GitHub の Issue を立てて知らせる。数字の書き換え（tools/data.py）は人が確かめてから行う。"""
import json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "js_scramble.json")
TXT = os.path.join(ROOT, "data", "js_scramble")
INDEX = "https://www.mod.go.jp/js/press/index.html"
UA = {"User-Agent": "Mozilla/5.0 (scramble-com press checker; https://xn--pckta2g7cl0c.com/)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def pdf_text(data):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data); f.flush()
        return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout

def issue(title, body):
    tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not tok or not repo:
        print("no token; skip issue"); return
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues", method="POST",
                                 data=json.dumps({"title": title, "body": body}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("issue:", r.status)

def main():
    first = not os.path.exists(OUT)
    data = {"items": []} if first else json.load(open(OUT, encoding="utf-8"))
    known = {i["url"] for i in data["items"]}
    try:
        page = get(INDEX).decode("utf-8", "ignore")
    except Exception as e:
        print("index error:", e, file=sys.stderr); sys.exit(1)
    found = []
    for href, title in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', page, re.S):
        title = re.sub(r"<[^>]+>|\s+", "", title)
        if "緊急発進" not in title: continue
        url = urllib.parse.urljoin(INDEX, href)
        if url in known or url in {f["url"] for f in found}: continue
        m = re.search(r"p(\d{4})(\d{2})(\d{2})_", url)
        found.append({"date": f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "", "title": title, "url": url})
    print("new:", len(found), "(first run)" if first else "")
    os.makedirs(TXT, exist_ok=True)
    found.sort(key=lambda x: x["date"], reverse=True)
    for i, f in enumerate(found):
        if first and i >= 3: continue  # 初回は直近3件だけ本文を保存
        try:
            text = pdf_text(get(f["url"]))
        except Exception as e:
            print("pdf error:", f["url"], e, file=sys.stderr); continue
        name = os.path.basename(urllib.parse.urlparse(f["url"]).path).replace(".pdf", ".txt")
        open(os.path.join(TXT, name), "w", encoding="utf-8").write(text)
        f["text"] = f"data/js_scramble/{name}"
        print("saved:", f["date"], f["title"])
    if found and not first:
        body = "統合幕僚監部の報道発表資料に、緊急発進の新しい資料が出ました。\n\n" + "\n".join(
            f"- {f['date']} [{f['title']}]({f['url']})" + (f"（本文テキスト: `{f['text']}`）" if f.get("text") else "") for f in found)
        body += "\n\n本文テキストを確かめて tools/data.py の数字を更新してください（AGENTS.md の「毎月の更新」）。"
        issue(f"緊急発進の新しい資料: {found[0]['title']}", body)
    data["items"] = sorted(data["items"] + found, key=lambda x: x["date"], reverse=True)[:300]
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    tmp = OUT + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)

if __name__ == "__main__":
    main()
