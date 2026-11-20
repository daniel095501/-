# 出發前，先查證

清大 112034058 工工大四 鄭宇辰

這是一個給初次自由行大學生的 LLM Wiki 與教學 HTML 簡報。先討論主題，再取得五份真實文件，經 AI 整理成六個相互連結的知識頁，最後由程式讀取 Wiki，建立14頁教學簡報。

## 從哪裡開始

- `index.html`：Wiki入口、搜尋與六個知識頁。
- `slides.html`：14頁教學、三題測驗、鍵盤翻頁與逐頁依據。
- `sources.html`：五份來源、日期、適用範圍與下載識別資料。
- `workflow.html`：流程、返回路徑、真實問題、修改與理解說明。
- `docs/report.md`：本次作業完整文字說明與反思。

瀏覽成果不需要 API 金鑰、安裝套件或登入。可以直接用瀏覽器開啟 `index.html`，也可以用本機伺服器或 GitHub Pages。所有網站內部連結採相對路徑。

## 知識與來源的關係

|來源|整理成的Wiki|教學重點|
|---|---|---|
|S01 領務局〈出國前小叮嚀〉|行前準備|先找官方查詢入口|
|S02 民航局〈旅客須知〉|搭機準備|一般提醒仍須核對實際航空公司|
|S03 長榮航空〈行李基本須知〉|行李資訊|區分託運與未託運，不把一家規定套用全部業者|
|S04 高鐵〈網路訂票〉|交通資訊|確認取票狀態及原文條件|
|S05〈氣象常識問答集〉|天氣資訊|降雨機率與雨量不同；舊教材用來教定義|

第六個 Wiki〈旅行資訊的四格查核法〉是本專案的方法整理，與原文事實分開標示。`F01`～`F05` 是來源事實，`M01`～`M03` 是本專案整理的方法。簡報共有32個知識點對應；相同知識點可出現在不同教學頁，不代表有32篇不同資料。

## 工作流

AI閱讀整理在這次協作對話中完成；程式負責下載、摘錄核對、Wiki建置、Wiki查詢、HTML生成與紀錄。沒有在背景呼叫另一個未揭露的模型，也不是訓練模型。

`scripts/build.py` 先建立 `wiki/*.md`，再從其中的 `claim` 區塊讀取知識，填入 `data/lesson.json`。每頁的查詢與結果保存在 `data/wiki-query-log.json`。不是把事先寫好的完整簡報直接貼到網站，也沒有讓簡報跳過 Wiki 取用搜尋結果。

這個loop包含AI／人工複核和程式驗證。程式遇到缺漏會停止並記錄返回節點；修正後再執行，不宣稱全自動自我修正。

## 檔案結構

```text
AGENTS.md                 新增與修改規則
sources.json              五份文件與必要短摘錄
raw/                      收錄摘錄、網址、版本、時間與雜湊
wiki/                     六篇知識頁的Markdown與HTML、目錄
data/claims.json          來源事實與方法知識點
data/source-review.json   與來源雜湊綁定的範圍審核
data/lesson-plan.json     教學結構與練習
data/lesson.json          從Wiki讀取知識後的教學內容
data/wiki-query-log.json  Wiki與簡報對應
data/*report.json         實際執行與檢查
docs/                     討論、修改、流程與反思
evidence/                 實際瀏覽器截圖及檢查紀錄
scripts/                  下載、建置、檢查與重跑程式
assets/                   共用樣式、原生JavaScript、圖示
```

## 重現本次建置

已收錄資料與審核結果可離線重建，只需 Python 3：

```sh
python scripts/run.py
python -m http.server 8000
```

開啟 `http://localhost:8000/`。程式會更新真實建置時間與紀錄，不會重新產生模型回答。

若要重新下載來源，先安裝PDF擷取套件，再執行：

```sh
python -m pip install -r requirements.txt
python scripts/run.py --refresh --cache-dir .cache
```

來源若改版或雜湊改變，應先核對原文、摘錄與適用範圍，重新審核 `data/source-review.json`，不能直接複製雜湊宣稱通過。確認後再重跑。完整下載只保存在不公開的快取，公開專案僅保留必要短摘錄。

## 實際檢查與限制

`data/ingest.json` 記錄五份文件實際HTTP下載與摘錄核對。`data/static-check.json` 記錄連結、頁面與知識對應檢查。`data/browser-qa.json` 記錄本機Chrome實測；`evidence/` 保留截圖與驗證程式。

檢查能確認結構及功能，不能自動保證語意永遠正確。規定可能更新，本次快照不是即時資訊服務。三題測驗與旅人案例是教學設計，不是使用者研究。

## 發布

將整個專案放在 GitHub 儲存庫的 `travel-wiki/` 資料夾，保留內部結構。以 GitHub Pages 發布後，首頁位於 `/travel-wiki/`，簡報位於 `/travel-wiki/slides.html`。本機測試通過不能代替公開網址檢查。

## AI協作

使用者提供作業要求，選定旅行主題和教學對象。AI協助來源閱讀、Wiki、教學設計、程式、實測與文字整理；反思與理解說明也由AI協助起草。實際討論摘要見 `docs/discussion.md`，不補造先前未發生的對話。
