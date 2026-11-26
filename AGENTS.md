# スクランブル.com（xn--pckta2g7cl0c.com）作業ルール

GitHub Pages の静的サイト。tools/build.py が tools/content/*.html から生成。
- tools/content/<name>.html → /<name>/（index はトップ）。1行目 title、2行目 description、本文は h1・p.updated・h2…、最後に section.sources
- 数字はすべて tools/data.py に集約（統合幕僚監部の公表資料から書き写す）。本文の {{YEAR_TABLE}} などが data.py から表・グラフになる
- 出典は data.py の SOURCES に登録し、本文では <li data-src="キー"></li> と書く
- 事実は防衛省・統合幕僚監部・内閣官房など政府の公式発表だけ。報道・Wikipedia・ブログは不可
- 外国機の意図や今後の見通しを推測で書かない。中立（特定の国・立場を支持・批判しない）
- 1ページ本文3,000文字以上を目標（規約ページを除く）

## 毎月の更新（統合幕僚監部「月間緊急発進状況」が翌月の中旬〜下旬に出る）
1. https://www.mod.go.jp/js/ で最新の月間緊急発進状況のPDFを確認
2. tools/data.py の M2026（合計・方面隊別・国別）に月を1つ追加し、M2026_ASOF と SOURCES["m202610"] を更新
3. 本文中の「10月までで577回」などの文章の数字を直す（grep で 577 などを探す）
4. python3 tools/build.py → push
年度のまとめ（4月ごろ）が出たら YEARS・COUNTRY に年度を追加し、M2026 を確定値で置き換え、新年度の月別を始める。
