# スクランブル.com（xn--pckta2g7cl0c.com）作業ルール

GitHub Pages の静的サイト。tools/build.py が tools/content/*.html から生成。
- tools/content/<name>.html → /<name>/（index はトップ）。1行目 title、2行目 description、本文は h1・p.updated・h2…、最後に section.sources
- 数字はすべて tools/data.py に集約（統合幕僚監部の公表資料から書き写す）。本文の {{YEAR_TABLE}} などが data.py から表・グラフになる
- 出典は data.py の SOURCES に登録し、本文では <li data-src="キー"></li> と書く
- 事実は防衛省・統合幕僚監部・内閣官房など政府の公式発表だけ。報道・Wikipedia・ブログは不可
- 外国機の意図や今後の見通しを推測で書かない。中立（特定の国・立場を支持・批判しない）
- 1ページ本文3,000文字以上を目標（規約ページを除く）

## 毎月の更新（自動）
- GitHub Actions（.github/workflows/js.yml、1日2回）が統合幕僚監部の報道発表資料を確認し、題名に「緊急発進」が入った新しいPDFの本文を data/js_scramble/ に保存する
- 「月間緊急発進状況」は tools/update_monthly.py が読み取り、検算（方面隊の合計・国地域の合計・合計列）がすべて合ったときだけ tools/m2026.json を書き換え、build してそのまま公開する
- 本文の今年度の数字は {{=式}}（tools/build.py の expr_ctx）で m2026.json から計算して入れている。今年度の回数を本文に直接書かないこと
- 読み取り失敗・年度が変わった・年度のまとめが出たときだけ Issue が立つ

## 年度の切り替え（年1回、4月ごろの年度のまとめのあと）
年度のまとめが出たら YEARS・COUNTRY に年度を追加し、M2025 を確定値に、m2026.json を新年度に切り替える（本文の「2026年度」「2025年度」の表記と update_monthly.FY も直す）。
