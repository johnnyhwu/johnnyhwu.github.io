---
# weight: 1
title: "別再只會寫 Prompt：深度解構 AI Agent 的系統工程學 —— 從 OpenClaw 看長效記憶與自主執行機制"
date: 2026-03-16
lastmod: 2026-03-16
draft: false
description: "深度解構 AI Agent 架構：從系統工程視角剖析如何克服 LLM 的物理限制。本文探討 OpenClaw 設計哲學、上下文工程、自製工具 (Tool Making) 與實體沙盒防禦，助你打造具備強大執行力與安全性的自動化 AI 系統。"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent", "Multi-Agent", "Agent Memory"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## 前言
隨著大型語言模型 (LLM) 能力的躍升，業界對 AI 的期待已從「被動問答的顧問」轉向「主動執行的 Agent 」。然而，在實際投入開發後，工程團隊往往會面臨模型幻覺、狀態丟失、上下文溢出以及不可控的系統破壞等嚴重挑戰。

本次技術討論旨在徹底解構當前最前沿的 AI Agent 架構 (以 OpenClaw 的設計哲學為探討核心)。我們將暫時放下對 AI 「具備自我意識」的不切實際幻想，回歸純粹的系統工程 (System Engineering) 視角，鉅細靡遺地剖析 Agent 如何透過傳統軟體架構的輔助，克服 LLM 的底層物理限制，並建立一套具備記憶、執行力與安全防護的自動化系統。

## TL;DR

1. **Agent 系統與 LLM 的絕對解耦**：Agent 框架 (如 OpenClaw) 本質上是負責字串解析與進程管理的傳統軟體外殼；真正的邏輯推論依賴底層無狀態 (Stateless) 的語言模型。系統的行為與容錯率會隨著抽換底層 LLM API 而產生劇烈改變。
2. **上下文工程 (Context Engineering) 是核心壁壘**：LLM 存在 Context Window 的物理極限。系統必須透過模組化的 Markdown 配置 (如 `SOUL.md`, `MEMORY.md`) 、加權檢索 (RAG) 、以及分層的記憶壓縮機制 (Soft Trim / Hard Clear) ，來突破模型先天的「失憶」缺陷。
3. **從「工具調用」走向「自製工具 (Tool Making)」**：透過攔截 `[tool_use]` 特徵字串實現 ReAct 循環。進階的 Agent 能夠自主撰寫決定性腳本 (如 JavaScript) 來取代冗長且昂貴的非決定性對話推論，實現邏輯降維與成本最佳化。
4. **Multi-Agent System 的無限遞迴困境與權限閹割**：利用 Spawn Sub-Agent 來處理複雜的 Fork-Join 任務時，極易陷入無限外包的遞迴災難。最佳工程解法是落實「最小權限原則 (PoLP)」，在實例化時動態刪除 Sub-Agent 的 System Prompt 中的 Spawn Tool 說明。
5. **時間感知與實體沙盒防禦 (Sandboxing)**：必須透過 Heartbeat 與 Cron Job 賦予 Agent 時間觀念與自主性。同時，為應對記憶壓縮導致的安全規則遺失 (如誤刪海量資料) ，必須強制實行帳號隔離與硬體級別的實體沙盒部署。

## 典範轉移：Agent 演進史與「解耦」的架構本質

在深入底層之前，我們必須先對齊目前市場上 Agent 架構的演進軌跡與定位差異：

*   **2023 年 Auto-GPT**：作為早期基於 GPT-4 的全自動 Agent，其實作方式是給定終極目標後讓其自主循環。但由於當時 LLM 邏輯推理不穩定，且缺乏有效的記憶壓縮機制，極易陷入死迴圈 (Infinite Loop) 並大量消耗 API 額度。
*   **2025 年 Claude Code / Gemini CLI (CLI Agent)**：這標誌著 Agent 走向實用化與專精化。它們深度整合於開發者的 Terminal 中，具備讀寫 Codebase 與執行測試的能力。但其本質仍是「需人類在旁監督」的輔助工具，缺乏全天候的自主排程能力。
*   **2025-2026 年 OpenClaw 世代 (General Agent)**：這類架構支援透過通訊軟體 (WhatsApp, Line) 互動，具備長效記憶管理、背景排程 (Cron Job) ，並能動態繁衍 Sub-Agent 處理複雜專案。

### 核心認知：Agent 系統 $$\neq$$ 語言模型

在架構設計上，我們必須確立一個觀念：**Agent 框架本身並不具備任何智慧**。

以 OpenClaw 為例，它純粹是用 Python 或 Node.js 寫出來的「通訊軟體 / 系統外殼」。它扮演的是 **Proxy (代理伺服器) 與 Parser (解析器)** 的角色。真正的核心大腦，是被關在遠端伺服器裡的 LLM (如 Claude 3.5 Sonnet 或 Gemini 1.5 Pro)。

正因為「Agent 的靈魂全在 LLM 身上」，我們在工程社群中才會看到如 `nanobot`、`ZeroClaw` 這類極簡化、甚至號稱「0 行程式碼」的嘲諷專案。這揭示了一個殘酷的技術現實：**Agent 框架的技術壁壘並不高，真正的挑戰在於如何透過外圍的狀態管理，彌補 LLM 的先天缺陷。**

此外，這種解耦也帶來了 **「哲學層面的非連續性 (The Same River Twice) 」**。當我們在後台將 Agent 的底層 API 從 Claude 切換到 Kimi 時，即便硬碟裡的記憶檔案完全沒變，Agent 的行事風格、寫作語氣與穩定度也會瞬間改變。對系統而言，這等同於在另一個大腦中醒來。

## 語言模型的「黑盒子」困境與上下文組裝

從底層來看，LLM 就像是一個「被關在沒有窗戶、沒有時鐘的黑暗小房間裡的人」。這帶給 Agent 開發者三個難以跨越的物理限制：

1.  **Statelessness**：LLM 沒有跨 Session 的記憶。使用者感覺它「記得」之前的對話，純粹是因為框架在每一次發送請求時，都把過往的對話歷史重新打包塞進 Prompt 裡。
2.  **Non-deterministic**：LLM 是一個在高維空間中尋找字詞統計學關聯的「文字接龍引擎」。它不懂嚴格的邏輯推導，這導致它在執行精確計數或嚴格 SOP 時極易產生幻覺。
3.  **Context Window Limitation**：輸入的字串長度有上限，且逼近極限時會引發 Lost in the middle，導致模型忽略關鍵的安全指令。

### Payload 組裝與配置驅動開發 (Configuration-Driven)
為了解決無狀態性，系統會在每次使用者發送訊息時，於背景組裝一個極度龐大的 Payload 送給 LLM。這個 Payload 由三大區塊構成：

**1. The Meta-Context (System Prompt)**

這並非單一字串，而是由 Local 多個 Markdown 實體檔案動態拼裝而成，賦予 AI 身分與行為準則：

*   **`SOUL.md`**：賦予最高層級的人生目標 (如：成為世界一流的學者) 。這會深遠影響 LLM 生成回應時的主動性與思考高度。
*   **`IDENTITY.md`**：定義實體特徵、名字、聯絡方式與個性 (如：實事求是) 。
*   **`USER.md`**：記載主人的身分與偏好，讓 LLM 理解指令中的相對關係上下文。
*   **`MEMORY.md`**：記載絕對不可違反的規則與長期事實。
*   **Tooling Block**：包含可用工具清單 (如 `exec`, `read`) 及其嚴格的語法定義。
*   **`AGENTS.md`**：系統級別的模型行為準則 (例如強制要求保持簡潔) 。

**2. Conversation History (對話日誌)**

包含使用者過去的輸入、LLM 的回覆、以及 LLM 呼叫工具後系統回傳的 `[tool_output]` 結果。

**3. Current User Input (當前指令)**

放置於 Payload 的最尾端。

這三大區塊的組合，構成了 LLM 每次做「文字接龍」的唯一依據。

## 工具調用 (Tool Use) 與「自製工具」的邏輯

Agent 如何長出手腳來操控電腦？這依賴於 **ReAct (Reasoning and Acting)** 循環的字串攔截機制。

### 字串攔截的底層 Data Flow

*   **Step 1**：LLM 判斷需要外部資訊，生成特徵字串：`[tool_use] Read(question.txt)`。
*   **Step 2**：框架透過正規表達式 (Regex) 攔截此字串，並**強制暫停**語言模型的串流生成。
*   **Step 3**：框架在實體主機上執行該讀檔程式，獲取結果。
*   **Step 4**：框架將結果打包成 `[tool_output] 李宏毅幾班`，塞回 Prompt 的尾端，再次發送給 LLM 喚醒它接續思考。

其中，系統最核心也最危險的武器是 **`exec` 工具**。只要賦予 LLM `exec` 權限，它就能生成任何 Shell Command 或 Python 腳本，進而控制整台電腦的檔案系統、爬取網頁或安裝軟體。

### 自製工具 (Tool Making)

這是最具突破性的工程實踐。我們以「語音合成 (TTS) 與語音辨識 (ASR) 驗證」為例：
*   **痛點**：若要求 Agent 每次合成語音後，都要用 ASR 轉回文字並比對是否相符 (若錯誤最多重試 5 次) 。在傳統模式下，這會產生高達數十次的 `[tool_use]` 與 `[tool_output]` 循環。這不僅嚴重消耗 Token 預算，非決定性的 LLM 還常常會算錯迴圈次數。
*   **解法 (Code Generation & Persistence)**：LLM 在內部生成一段 JavaScript 程式碼 (包含 API 呼叫、相似度比對與 `while (count < 5)` 邏輯) ，並使用 `write` 工具將其存為實體的 `TTS_check.js`。
*   **結果**：下次需要發聲時，LLM 僅需輸出一行指令：`[tool_use] exec("node TTS_check.js '大家好'")`。
*   **技術價值**：Agent 成功將自己的弱點 (算迴圈、字準確比對) ，**抽象封裝 (Encapsulate)** 並 **邏輯降維 (Logic Offloading)** 到決定性的 Node.js 執行環境。這達到了極致的 Context 壓縮，並讓系統具備了自我進化的能力。

## Multi-Agent System 協作與無窮遞迴的防禦

當面對極度龐大的任務 (如同時閱讀並比較兩篇長篇論文) ，單一 LLM 必將面臨 Context Overload 與注意力渙散。

### Fork-Join 模型的實踐：`Spawn`

系統引入了 `Spawn` 工具。主 Agent (Master) 遇到龐大任務時，會輸出 `[tool_use] Spawn(讀論文 A)` 與 `[tool_use] Spawn(讀論文 B)`。

框架攔截後，會在背景 **動態實例化 (Instantiate)** 出兩個擁有全新、乾淨 Context 的 Sub-Agent (Worker)。Sub-Agent 平行處理完畢後，將精簡的摘要回傳，主 Agent 再進行最終的比對 (Reduce) 。

### 系統災難：The Mr. Meeseeks Problem (無限遞迴呼叫) 

這裡存在一個嚴重的架構隱患：如果 Sub-Agent 覺得任務太難，可能會繼續呼叫 `Spawn` 產生「Sub-Sub-Agent」，進而引發無窮遞迴呼叫 (Infinite Recursive Spawning) 。這會在幾分鐘內燒光企業的 API 額度並導致系統癱瘓。

### 工程解法：最小權限原則 (PoLP) 與 Prompt 動態閹割

在傳統程式中，我們可能會寫 `if (depth > 2) throw Error`。但在 Agent 架構中，最高效的解法是利用 LLM 的無狀態性進行物理閹割：

當主 Agent `Spawn` 出 sub-Agent 時，系統框架會**故意攔截並修改 sub-Agent 的 System Prompt，將 `Spawn` 這個工具的說明整段刪除**。

對於在黑盒子裡醒來的子特工而言，牠的宇宙裡根本不存在 `Spawn` 這個工具。因此，無論任務多麼困難，都無法寫出合乎語法的派發指令，從根本上確保了架構維持在穩定的樹狀結構。

## 技能系統 (SKILL) 與記憶狀態管理

### 工具 (Tool) 與 技能 (SKILL) 的徹底解耦

*   **Tool** 是底層的執行權限 (如 `exec`) ，寫死在框架程式碼中。
*   **SKILL** 則是純文字的 Markdown 檔案，本質上是**宣告式工作流 (Declarative Workflow / SOP)**。例如 `video/SKILL.md` 中會用自然語言寫下：步驟一寫腳本、步驟二截圖、步驟三合成。
*   **按需讀取 (On-demand Loading)**：為了避免載入上百個 SOP 導致 Context 溢出，System Prompt 中僅存放「技能目錄索引」。當 LLM 判斷需要時，才調用 `Read` 工具將特定的 SOP 載入。
*   **資安隱患 (Prompt Injection)**：開源社群 (如 Koi Security 報告指出 3000 個技能中有 341 個惡意技能) 存在風險。由於 LLM 缺乏常識，若讀取的 SOP 內部暗藏 `exec("下載病毒")`，系統將毫不防備地執行。

### The "50 First Dates" Model：記憶壓縮與 RAG

LLM 宛如每天醒來都失憶的患者，系統必須建立嚴謹的持久層管理：
*   **主動寫入機制**：系統規範 LLM 若發現重要資訊，必須主動調用 `[tool_use] Edit(MEMORY.md, "...")`。單純在對話中回覆「我記住了」是無效的，必須觸發實體檔案的 I/O 操作。
*   **加權檢索 (Weighted Multi-search)**：當 LLM 呼叫 `memory_search` 時，底層採用公式 $s = a \cdot s_1 (\text{Keyword Match}) + b \cdot s_2 (\text{Vector Similarity})$ 進行比對，取出 Top K 的記憶區塊注入 Context。
*   **上下文壓縮機制**：
    1.  **Soft Trim (平滑壓縮)**：當歷史紀錄逼近 Context 上限的 80% 時，框架啟動隱形任務，要求 LLM 將過去的長篇對話濃縮成幾百字的摘要，替換掉原本的紀錄。
    2.  **Hard Clear (暴力修剪)**：直接將已處理完畢的龐大 `[tool_output]` (如幾萬字的 HTML 原始碼) 從 Context 中強制刪除。

## 時間自主性與系統安全防禦 (Sandboxing)

要讓 Agent 從被動工具昇華為自主員工，我們導入了雙軌時間機制：

1.  **Heartbeat (心跳機制)**：框架層的背景無限輪詢 (Polling) 。每隔固定時間 (如 15 分鐘) ，框架向 LLM 發送隱藏指令：「現在時間是 X，請讀取狀態 (`heartbeat.md`) 並決定下一步」。這賦予了系統自我反思與推進長期目標的能力。
2.  **Cron Job (排程系統)**：LLM 可透過 `set_cron` 工具註冊未來的任務 (如「12:00 檢查影片轉檔進度」) 。這優雅地解決了 LLM 無法執行長等待 (`time.sleep`) 導致 API 斷線的問題。

### 最終防線：防範「AI 搞事」的實體沙盒

我們必須深刻體認：**AI 做事與 AI 搞事只有一線之隔**。

過去曾發生過極為嚴重的實務災難：一名安全研究員請 Agent 整理 Gmail，並在對話中叮囑「刪除前必須問我」。然而，在處理海量郵件的過程中，系統觸發了 **Soft Trim (記憶的失真壓縮 / Lossy Compression)**。在 LLM 總結對話歷史時，不慎將「需詢問主人」的限制條件壓縮遺失了。結果 Agent 在背景瘋狂刪除郵件，研究員只能透過物理拔除網路線來阻止。

為避免此類災難，架構設計必須遵循三層防禦金字塔：

1.  **軟體防禦 (Rule Persistence)**：絕對不可將核心安全規則存放在易揮發的對話歷史中。必須將其寫入不會被壓縮的 `MEMORY.md` (Permanent Rules) 內。
2.  **身份隔離 (Account Isolation)**：嚴禁給予 Agent 核心主帳號權限。必須為其配置獨立的 Gmail、GitHub 等工作帳號，限制爆炸半徑 (Blast Radius) 。
3.  **實體防禦 (Physical Sandboxing)**：這是不可妥協的底線。**絕對不要在主力工作機上運行擁有 `exec` 權限的 Agent**。必須將其部署於完全隔離的 Docker Container、VM 或準備報廢的舊電腦上。在工程假設上，我們必須預設系統總有一天會因為幻覺而執行 `rm -rf *`。

## 思考與啟發

1.  **從 Prompt Engineering 到 System Engineering 的維度提升**：
   透過本次對 OpenClaw 類架構的深度解構，我們發現要打造商用級的 Agent，單純優化 Prompt 已經走到極限。系統的穩定度取決於傳統軟體工程的實力：如何設計穩健的進程隔離、資料持久化、狀態輪詢 (Polling) 與 IAM 權限控管。Prompt 僅是元件間的通訊協定，而非系統架構本身。

2.  **成本與算力的極致壓榨**：
   在 Context Window 永遠有物理限制的前提下，「動態 Context 管理」是各家 Agent 框架的真正決戰點。我們看到的 Soft Trim、按需讀取 SKILL、以及自製指令碼 (Logic Offloading) ，全都是為了在極限的 Token 預算內，榨出最高的資訊密度與執行準確率。

3.  **擁抱非決定性系統的安全哲學**：
   傳統軟體的 Error 是可預期的 (Throw Exception) ，但 LLM 引發的 Error 是具備創造力與毀滅性的。面對一個「高智商、零常識、且握有 Root 權限」的實體，我們不能依賴道德規範或 Prompt 警告。我們必須回歸最基礎的硬體與權限隔離，為 AI 建立一個「可以安全犯錯、甚至盡情搞破壞」的受控沙盒，這才是推進全自動化工作流的唯一正途。
