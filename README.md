# 🏮 財神爺的金頭腦 (Fortune God's Quiz Bot)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://img.shields.io/badge/License-MIT-blue.svg)
[![Python](https://img.shields.io/badge/Python-3.9%2B-yellow.svg)](https://img.shields.io/badge/Python-3.9%2B-yellow.svg)
[![Line API](https://img.shields.io/badge/LINE-Messaging%20API-green.svg)](https://img.shields.io/badge/LINE-Messaging%20API-green.svg)
[![Gemini API](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)

**財神爺的金頭腦** 是一款專為農曆新年設計、主打「長輩友善」的 LINE 互動猜謎機器人。  
透過整合 **Google Gemini AI** 動態生成懷舊題庫，並巧妙結合 **LINE LIFF** 網頁技術來大幅降低 LINE 官方帳號的訊息成本，讓長輩在過年期間輕鬆體驗數位互動的樂趣。

---

## ✨ 特色功能

- **🤖 AI 動態出題**：串接 Gemini 1.5 Flash，根據長輩選擇的「年代」與「主題」即時生成題目，告別傳統寫死的靜態題庫。
- **👵 長輩友善 UI**：全面採用全螢幕 LIFF 網頁與 Flex Message 大按鈕，免打字、零門檻，點擊即玩。
- **💰 極致的成本控制 (LIFF 應用)**：將「參數收集（年代/主題）」的流程放進 LIFF 網頁中，透過網頁代替使用者發言，成功將每局遊戲的推播成本降至最低（單局僅需消耗 1~2 則訊息）。
- **⚡ 無狀態架構 (Stateless)**：捨棄複雜的記憶體或資料庫狀態管理，每次請求獨立處理，極度適合部署於 Render 等 Serverless 雲端平台，冷啟動後運行依然極速。

---

## 🎨 UI / UX 重點

### 喜氣網頁設計 (LIFF)

- 主題色系：過年紅 (`#D32F2F`) 搭配財神金 (`#FFC107`)。
- 無縫體驗：選完題目後，LIFF 網頁自動關閉並連動聊天室的「出題中...」提示，覆蓋 AI 生成的等待時間。

### 數位紅包題目卡 (Flex Message)

- 高對比大字體：題目與選項皆採用 `md`~`xl` 大字體。
- URL Query 資料壓縮：運用 Postback URL 編碼技巧 (`ans&c=1&exp=...`)，突破 LINE Postback 資料長度限制，將解答與 AI 詳解隱藏於按鈕中。

---

## ⚙️ 技術架構

- **語言**：Python 3.9+
- **框架**：Flask + Gunicorn
- **AI**：Google Gemini API (`google-genai` 新版 SDK)
- **介面**：LINE Messaging API (Flex Message) + LINE Login (LIFF HTML/JS)
- **部署**：Render (Web Service)
- **資源策略**：無狀態設計 (Stateless)，完美適應 Serverless 冷啟動機制，極大化節省免費雲端資源。

---

## 🚀 快速開始

### 1. 環境需求

- Python 3.9+
- LINE Developers 帳號（需建立 **Messaging API** Channel 與 **LINE Login (LIFF)** Channel）
- Google AI Studio API Key（Gemini API）

### 2. 安裝依賴

極度精簡的套件清單，確保建置速度最快：

```bash
pip install -r requirements.txt
```

### 3. 設定環境變數

在部署平台（如 Render）或本機環境 `.env` 中設定：

- `LINE_CHANNEL_ACCESS_TOKEN` — LINE Bot 的 Access Token
- `LINE_CHANNEL_SECRET` — LINE Bot 的 Channel Secret
- `LIFF_ID` — LINE LIFF 的 App ID
- `GEMINI_API_KEY` — Google Gemini API Key

---

### 4. 本地執行（開發測試）

```bash
python app.py
```

---

## ☁️ 部署教學（Render 範例）

1. 將程式碼推到 GitHub。
2. 在 Render 建立 Web Service，連結 repo。
3. Build Command：

    ```bash
    pip install -r requirements.txt
    ```

4. Start Command（生產環境必備）：

    ```bash
    gunicorn app:app
    ```

5. 在 Render 的 Environment 設定上面列出的 4 個環境變數。
6. 部署完成後，進行以下兩項設定：

    - 將 LINE Developers (Messaging API) 的 Webhook URL 設為：
      `https://你的網址.onrender.com/callback`
    - 將 LINE Developers (LINE Login > LIFF) 的 Endpoint URL 設為：
      `https://你的網址.onrender.com/liff`

---

### 🔔 關於 Render 免費版睡眠機制（冷啟動）

本專案極度輕量，非常適合部署於 Render 免費方案。

**請注意：** Render 免費版 Web Service 在閒置 15 分鐘後會自動進入「睡眠狀態」以節省資源（Render 每月總免費額度為 750 小時）。
為避免耗盡免費額度，**本專案不建議使用 UptimeRobot 等監控服務持續喚醒**。

**對體驗的影響：**
當機器人處於睡眠狀態時，長輩的「第一次點擊（開啟 LIFF 網頁）」大約需要等待 **30~50 秒（冷啟動）** 才會載入畫面。只要伺服器喚醒後，後續的互動與 AI 出題就會恢復極速順暢！

---

### 🎮 遊戲互動流程

1. **觸發遊戲**：長輩點擊 LINE 官方帳號下方的**圖文選單 (Rich Menu)**，開啟 LIFF 網頁。
2. **選擇主題**：在全螢幕紅色網頁中，選擇挑戰的「年代」與「類型」，點擊「擲筊求題」。
3. **隱藏發送**：LIFF 自動關閉，並替長輩在聊天室送出隱藏指令（如 `#出題 1980年代 台語俗諺`）。
4. **AI 生成**：機器人回覆等待提示，同時呼叫 Gemini AI 動態生成 4 選 1 題目。
5. **作答與回饋**：長輩點擊 Flex Message 上的選項，機器人驗證對錯並給出幽默的解答補充。

---

### 📁 專案結構

```text
.
├─ app.py                # 核心後端邏輯 (Flask + LINE SDK + Gemini API)
├─ requirements.txt      # 僅含 4 項核心依賴
├─ templates/
│  └─ liff.html          # LIFF 前端網頁 (長輩設定介面)
├─ LICENSE               # MIT 授權
└─ README.md             # 本文件
```

---

### ⚠️ 注意事項

- **LIFF 權限設定**：在建立 LIFF App 時，務必勾選 `chat_message.write` 權限，否則網頁無法代替長輩發送出題指令。
- **圖文選單綁定**：強烈建議在 LINE 官方帳號後台設定圖文選單，並將其動作設為「連結」，貼上你的 LIFF URL ( `https://liff.line.me/你的ID` )，這是體驗最流暢的做法。

---

### 📄 License

本專案採用 MIT License。詳見 [LICENSE](LICENSE) 檔案。

---

讓財神爺陪長輩開心過好年！🏮🎲
