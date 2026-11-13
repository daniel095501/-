# 啟程前｜旅行準備指南

以 AGENTS.md 規範內容、版型與開發流程的靜態小專案。清大 112034058 工工大四 鄭宇辰。

## 目前內容

目前有四篇：行李整理、交通轉乘、行前檢查，以及依相同規則延伸的住宿入住確認。每篇都有問題說明、準備步驟、勾選清單、常見漏項及需要核對的資訊。新增第四篇時，沒有修改版型、CSS、JavaScript 或產生器。

## 開發與新增

先讀 [AGENTS.md](AGENTS.md)。不需要安裝套件。

```bash
python scripts/build.py
python scripts/check.py
python -m http.server 8765
```

本機開啟 `http://localhost:8765/`。新增指南只需在 `content/guides/` 加入合約一致的 JSON，重建後首頁、導覽與相關指南會一起更新。不要直接編輯產出的 HTML。

## 部署與資料

完整資料夾部署到 `daniel095501/-` 的 `travel-guide/`，沿用既有 GitHub Pages。所有站內路徑皆相對定位，支援儲存庫子路徑。網站無後端；清單只保存在同一瀏覽器的 localStorage，可逐篇重設，不會跨裝置同步。

本網站為一般準備建議，不包含即時票價、班次或目的地規定。內容與程式由 AI 協助製作，個人選題與需求來自使用者；詳見 `docs/ai-collaboration.md`，實際延伸過程見 `docs/extension-log.md`。

## 架構

```text
AGENTS.md                 AI 維護規則
content/guides/*.json      每篇指南的內容來源
templates/                共用頁面版型
assets/                   共用 CSS 與 JavaScript
scripts/build.py          靜態頁面產生器
scripts/check.py          結構、資料與連結檢查
index.html                產出的首頁
guides/*.html             產出的指南頁
docs/                     說明、協作與驗證紀錄
```

技術依據：[GitHub Pages 官方說明](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)。
