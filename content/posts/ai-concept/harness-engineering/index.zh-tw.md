---
# weight: 1
title: "掌握 Harness Engineering：結合 Ralph Loop 與 MemRL，打造具備持續學習能力的 AI Agent"
date: 2026-04-05
lastmod: 2026-04-05
draft: false
description: "深入探討 2026 AI Agent 系統工程新典範：結合 Model、Harness 與 Context 的三層架構。解析 Ralph Loop 與 MemRL 演算法，助您解決 AI 幻覺與上下文腐爛，建構具備持續學習能力的工業級 Agent。"
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent", "Multi-Agent", "Agent Memory"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## 前言

*   **Agent 發展的典範轉移：** 從單純追求「更聰明的大模型」，轉向「建構更完善的系統工程」。真正的智能不僅來自 Weights，更來自系統的記憶與反饋機制。
*   **核心痛點：** AI Agent 在工業界落地時面臨的兩大難題：
    1.  **無狀態與幻覺：** Agent 容易在同一個坑裡跌倒兩次，且單純的 RAG 會引發「語義噪音」。
    2.  **規模化與穩定性：** 複雜任務導致 Context Rot (上下文腐爛)，且微調 (Fine-tuning) 模型成本極高、容易引發災難性遺忘。
*   **本筆記目標：** 結合 [《MemRL》論文](../mem-rl/) 的演算法設計，以及 LangChain 的 [《Agent Harness》](https://blog.langchain.com/the-anatomy-of-an-agent-harness/) 與 [《Continual Learning》](https://blog.langchain.com/continual-learning-for-ai-agents/) 系統觀，提供一份從「記憶檢索」到「執行腳手架」的全方位架構藍圖。

## Agent 系統的三層架構解剖

在傳統軟體開發中，我們關注「程式碼 + 資料庫」；在早期的 AI 開發中，我們關注「模型」。但在 2026 年的 Agent 工程實踐中，我們必須遵循這個黃金公式：

> **Agent = Model + Harness + Context**

這三者的關係可以類比為：**Model 是大腦的神經元，Harness 是肉體與感官，Context 則是記憶與當下的感知。**

### Model (模型層)：凍結的大腦與推理引擎

Model 是系統的決策核心，負責將輸入的文字序列轉化為邏輯推理或工具呼叫。

*   **工業界現況：凍結 (Frozen) 是常態**
    在生產環境中，我們通常將 Model 視為「不可變的基礎設施 (Immutable Infrastructure)」。原因在於：
    1.  **災難性遺忘 (Catastrophic Forgetting)：** 微調 (Fine-tuning) 模型來學習新規則，極易破壞它原本的基礎推理能力。
    2.  **算力與延遲：** 頻繁微調模型會導致 MLOps 成本飆升。
*   **模型與腳手架的深度耦合 (Post-training Alignment)：**
    這是目前最硬核的觀察。如 Claude 3.5 Sonnet 這類頂尖模型，在後訓練階段 (RLHF) 就已經被放進特定的 Harness 中練習。
    *   **案例：** Claude 3.5 被訓練為高度偏好 `str_replace` 或 `apply_patch` 這種特定的檔案修改格式。如果你換成 OpenAI 模型，即使模型智商一樣，它可能因為無法精準產生符合該格式的字串而導致 Harness 解析失敗。這就是所謂的 **「腳手架依賴 (Harness-specific optimization)」**。

### Harness (腳手架層)：Agent 的維生系統與控制中樞

Harness 是所有包裝在模型外圍的程式碼與基礎設施。它是 Agent 能夠從「說說而已」變成「實際行動」的關鍵。

#### Infrastructure
*   **Filesystem** 模型是無狀態的 (Stateless)。Harness 必須提供一個持久化的工作目錄。Agent 的進度不應存在 Prompt 裡，而應存在磁碟上的檔案（如 `CLAUDE.md` 或 `TODO.json`）。
*   **Sandboxes**：Harness 負責調度 Docker 或虛擬機，讓模型產生的 Bash 指令或 Python 代碼能安全執行。

#### Action Space & MCP
*   **工具封裝**：Harness 將 API 封裝成模型可理解的 JSON Schema。
*   **漸進式揭露 (Progressive Disclosure)**： 為了節省 Token，Harness 不會一次給模型 100 個工具，而是先給一個 `list_tools`，讓模型需要時才動態載入特定工具的定義（Just-in-Time Injection）。

#### Orchestration & Hooks
*   **Middleware (中介軟體)**：Harness 會在模型輸出後進行「格式攔截」。
    *   **案例**：如果模型輸出了一個超長的日誌 (Log)，Harness 會主動執行 **Tool Call Offloading**，只把 Log 的頭尾存入 Context，其餘存入檔案，避免模型因上下文過載而變笨。
*   **自我驗證 (Self-Verification)**：Harness 可以在模型回覆使用者前，自動跑一遍測試腳本 (Test Suite)，如果報錯，直接把 Error 拋回 Ralph Loop。

### Context (上下文/記憶層)：動態經驗的注入

Context 是 Harness 根據當前任務，從外部動態拼湊出來給 Model 的輸入。

*   **Hierarchical Memory Isolation：**
    在企業級應用中，記憶體必須根據隱私權限進行分層：
    1.  **Agent-level：** 通用的最佳實踐、安全性原則。
    2.  **Org-level：** 內部專案標準、專屬 API 文檔。
    3.  **User-level：** 使用者的編碼偏好、歷史操作習慣。
*   **Injection Logic：**
    Harness 會在發送請求給 Model 前，執行一次檢索（例如用 [MemRL 算法](../mem-rl/)），將最相關的高效能經驗 (High-utility experiences) 注入 Context。

### Harness Engineering Pseudo-code

```python
# Harness 內部的控制邏輯 (Pseudo-code)
def run_agent_loop(user_input):
    context = load_hierarchical_memory(user_id, org_id) # 載入多層級記憶
    base_tools = ["list_skills", "read_file"] # 初始只給最少量的工具
    
    while True:
        # 1. 拼湊最終給模型的 Prompt
        prompt = assemble_prompt(user_input, context, base_tools)
        
        # 2. 模型決策
        response = model.call(prompt)
        
        # 3. Harness 攔截處理 (Hooks)
        if response.calls_tool == "list_skills":
            # 漸進式揭露：發現模型需要資料庫工具，動態注入定義
            db_tool_definition = fetch_tool_schema("database_query_tool")
            base_tools.append(db_tool_definition)
            continue # 重新開始迴圈，不消耗外部回覆
            
        if response.has_long_output:
            # 防腐機制：自動截斷過長輸出 (Head/Tail Truncation)
            response.content = truncate_log(response.content)
            
        # 4. 執行並獲得反饋 (Observation)
        result = sandbox.execute(response.action)
        context.update_short_term_memory(response.action, result)
```

## Context 層的持續學習 —— MemRL 演算法實踐

### 核心哲學：從「相似性」轉向「實用性」 (Utility-Driven)

傳統的 RAG 記憶體有一個根本性的缺陷：**語義相似 (Semantic Similarity) \( \neq \) 解決問題的效用 (Functional Utility)**。

*   **痛點：** 如果 Agent 曾經用一個錯誤的方法嘗試解決某個 SQL 查詢任務，傳統 RAG 下次遇到相似任務時，依然會因為「語義接近」而把錯誤的經驗檢索出來餵給模型。
*   **解法 (M-MDP)：** 將記憶建模為 **Memory-Based MDP**，每一條經驗不再只是 `(Vector, Content)`，而是三元組：**`(Intent, Experience, Utility/Q-value)`**。
    *   **Intent (意圖):** 原始任務的向量特徵。
    *   **Experience (經驗):** 執行的軌跡 (Traces)、成功的代碼或失敗的反思。
    *   **Utility/Q-value (效用值):** 該經驗在歷史中幫助任務成功的機率與回報。

### 雙階段檢索機制 (Two-Phase Retrieval)

為了平衡「搜尋速度」與「經驗質量」，我們在 Harness 中實作兩階段過濾：

#### Phase A: Similarity-Based Recall (語義召回 - 粗篩)
*   **動作：** 在 Vector DB 中執行 Top-k1 的 Cosine Similarity 搜尋。
*   **目的：** 作為「守門員」，確保撈出來的經驗在業務邏輯上是相關的。
*   **工程 Trick：** 設定一個硬性的相似度閾值 \( \delta \)（例如 0.38），低於此值的經驗直接丟棄，防止 Agent 被完全不相干的「高分回憶」干擾。

#### Phase B: Value-Aware Selection (價值感知選擇 - 精排)
*   **動作：** 對候選經驗進行加權打分。
*   **公式：** $$ Score = (1-\lambda) \cdot \text{Normalized\_Sim} + \lambda \cdot \text{Normalized\_Q\_value} $$
*   **意義：** \(\lambda\) 控制了 Agent 的「執拗程度」。
    *   若 \(\lambda=0.5\)，系統會同時考慮「長得像不像」與「過去成不成功」。
    *   這能有效過濾掉那些「語義噪音」——即長得像但實際上會導致失敗的經驗。

### Q-Value 動態更新規則 (Non-Parametric Learning)

這是 Agent 自進化的燃料。我們不更新權重，而是更新 Vector DB 裡的 **Metadata (Q-value 欄位)**。

*   **更新公式 (Monte Carlo / EMA)：**

    $$Q_{new} = Q_{old} + \alpha(R - Q_{old})$$

    *   \(R\) (Reward): 環境給予的反饋（成功 = +1, 失敗 = -1）。
    *   \(\alpha\) (Learning Rate): 記憶的更新速度。
*   **工程實作 (Runtime Update)：**
    當 Ralph Loop 完成一次任務並獲得驗證結果（例如 Test Suite 通過），Harness 會立刻回頭更新剛才被檢索出來的那幾條記憶。
    *   **優勢：** 這是 **"Hot-path" (即時學習)**。Agent 下一秒處理相似任務時，Q-value 已經更新，它會立刻避開剛才失敗的路徑。

### 學習失敗：高價值失敗經驗 (Near-Misses)

MemRL 論文中最具工程啟發的點在於：**失敗的經驗可能比成功的更有價值。**

*   **Failure Reflection (失敗反思)：**
    當任務失敗時，Harness 派一個 LLM 去分析 Traces，生成一段 `[PATTERN TO AVOID]`。
*   **記憶體寫入：**
    這段失敗反思會被賦予一個初始 Q-value。即使它是「失敗」的，但因為它明確告訴 Agent「不要做什麼」，它在相似情境下的決策效用極高。
*   **案例：**
    *   *經驗 A (成功):* 「直接用 `sed` 替換 config。」 (Q: 0.8)
    *   *經驗 B (失敗反思):* 「注意：`sed` 會略過被註釋掉的行，建議先取消註釋再替換。」 (Q: 0.95)
    *   **結果：** 下次 Agent 會優先讀取經驗 B，避免了潛在的 Bug。

### 實作範例：記憶體層級與更新時機

在 2026 年的企業架構中，我們會結合 **Hot-path** 與 **Dreaming**：

| 層次 | 學習時機 (When) | 處理內容 (What) | 目的 |
| :--- | :--- | :--- | :--- |
| **Hot-path** | 任務完成的瞬間 (Runtime) | 更新現有記憶的 **Q-value** | 即時糾錯，避免連續犯錯。 |
| **Dreaming** | 離線批次 (Offline/Daily) | 掃描 Traces，將多條相似經驗 **總結(Summarize)** 成一條高階規則 | 壓縮 Context 空間，對抗「記憶膨脹」。 |

### MemRL Q-Value Update Pseudo Code

```python
def post_task_learning(task_trace, feedback_reward):
    # 1. 取得本次任務中「被選中並注入 Context」的經驗 IDs
    retrieved_memory_ids = task_trace.metadata["retrieved_ids"]
    
    # 2. 執行 Non-Parametric RL 更新
    alpha = 0.3 # 學習率
    for mem_id in retrieved_memory_ids:
        old_q = vector_db.get_metadata(mem_id, "q_value")
        # 計算新的 Q 值
        new_q = old_q + alpha * (feedback_reward - old_q)
        # 寫回 Vector DB 的 Metadata
        vector_db.update_metadata(mem_id, {"q_value": new_q})
        
    # 3. 如果失敗，觸發失敗反思並寫入新經驗
    if feedback_reward < 0:
        reflection = llm.generate_reflection(task_trace)
        vector_db.add_new_experience(
            intent=task_trace.intent,
            content=reflection,
            initial_q=0.5 # 給予中等初始權重，引發下次嘗試
        )
```

## Harness 層工程技巧

### Ralph Loop：The Orchestrator

Ralph Loop 是一種對抗「多智能體複雜度陷阱」的架構心法。它主張 **「大道理不如一個強健的迴圈」**。

*   **核心理念：Monolithic > Multi-Agent**
    *   **痛點：** 過早引入多個 Agents 互相對話會增加系統的隨機性 (Entropy)，導致除錯困難與不穩定。
    *   **Ralph 模式：** 讓一個強大的模型 (如 Claude 3.5 或 GPT-5) 在一個單純的 `while` 迴圈中運作。每個迴圈只做一件事：**「觀察 → 思考 → 行動 → 獲得反饋」**。
*   **「丟回轉盤上 (Throw it back on the wheel)」：**
    *   當 Agent 在迴圈中失敗或報錯時，Harness 不會崩潰，而是捕獲 Error，重新組裝上下文，然後「再次拋入迴圈」。這讓軟體像陶土一樣，透過重複的 Loop 不斷被修整，直到符合驗證標準 (Validation)。

### Battling Context Rot

上下文空間（Context Window）是極度昂貴且脆弱的資源。過長的上下文會導致模型的 **Reasoning Degradation**。Harness 必須擔任「過濾器」。

#### Tool Call Offloading

*   **工程 Trick：Head/Tail Truncation**
    *   如果 Agent 執行 `cat log.txt` 回傳了 5 萬字，Harness 會攔截這個輸出。
    *   **作法：** 只保留 Log 的 **前 500 字 (Head)** 與 **後 500 字 (Tail)** 丟入 Prompt，其餘內容直接存入硬碟。
    *   **理由：** 錯誤訊息的核心通常在開始（指令狀態）與結尾（Stacktrace），中間的冗長內容只會干擾模型注意力。

#### Just-In-Time (JIT) Tool Injection

*   **作法：** 初始 System Prompt 只給予最基礎的導航工具。當 Agent 意識到需要特定技能時（例如：需操作 PDF），Harness 才動態將 PDF 處理工具的 JSON Schema 注入 Context。
*   **目的：** 減少開局的 Token 負擔，確保模型保留最高智商處理核心邏輯。

### Git-based State & Sandboxes

Agent 需要一個「輸得起」的環境。Harness 必須提供強大的撤銷與分支能力。

#### Rollback & Branching
*   **進階實作：** Harness 將 Agent 的工作目錄與 Git 綁定。
*   **機制：** 當 Agent 準備進行高風險的重構 (Refactor) 時，Harness 先偷偷執行 `git checkout -b experiment`。
*   **自動回滾：** 如果執行測試失敗且 Agent 無法在 3 個迴圈內修復，Harness 自動執行 `git reset --hard`。這讓 Agent 能在失敗後「無痛重啟」，徹底解決長線任務卡死的難題。

#### Sandbox Fan-out
*   **作法：** 利用 Docker 或 VM 提供獨立執行環境。
*   **價值：** 當 Agent 需要嘗試多種解法時，Harness 可以瞬間啟動 5 個平行沙箱，讓 Agent 同時測試 5 種程式碼分支，最後取成功的那一個合併回主幹。

### Harness Meta-Optimization

當 Agent 表現不好時，工程師不應優先去改模型，而是 **「編程這個迴圈 (Programming the loop)」**。

*   **修復失效域 (Failure Domain)：**
    *   如果 Agent 總是看不懂某個 API 的報錯訊息，你應該去修改 Harness 裡該工具的 `Error Message` 定義，讓報錯變得更具「指導性」。
*   **ACI (Agent-Computer Interface) 優化：**
    *   研究顯示，給模型一個「專為它設計的文字介面（如簡化的 `ls -R`）」比給它一個「人類用的 GUI 截圖」效能更高。這就是 **Harness Engineering 的核心價值**。

### Ralph Loop Framework Pseudo Code

```python
def ralph_loop_harness(task_goal):
    # 1. 準備 Git 乾淨環境與 Sandbox
    repo = git.initialize_workspace()
    sandbox = docker.create_sandbox()
    
    while not task_completed:
        # 2. 準備上下文 (包含 Log 截斷處理)
        obs = repo.get_current_state()
        context = prepare_lean_context(task_goal, obs)
        
        # 3. LLM 思考與行動
        thought_and_action = model.generate(context)
        
        # 4. 攔截並執行 (Git Branching 為例)
        if is_high_risk_action(thought_and_action):
            repo.create_checkpoint_branch()
            
        # 5. 執行獲取反饋 (Observation)
        result = sandbox.execute(thought_and_action.code)
        
        # 6. 自動化檢核 (Self-Verification)
        if result.exit_code != 0:
            # 失敗了？不要崩潰，把錯誤丟回 Loop 讓它修
            # 如果失敗次數過多，觸發 Harness 層的回滾
            if retry_count > threshold:
                repo.rollback_to_last_stable()
                task_goal.append_hint("Last attempt failed, try a different approach.")
            continue 
            
        task_completed = verify_with_tests(repo)
```

## 結論

### 核心觀念收斂：Agent 工程的範式轉移

在 2026 年的 Agent 開發語境下，我們必須承認一個現實：**單純依賴「更強大的模型」已經無法解決複雜的長線任務 (Long-horizon tasks)。** 真正的勝負在於系統工程的深度。

*   **Model 是凍結的引擎：** 我們不再幻想透過微調 (Fine-tuning) 來解決每天都在變化的業務邏輯，因為代價太高、風險太大。
*   **Harness 是強健的骨架：** 透過 **Ralph Loop** 的單體迴圈、**Git** 的狀態回滾、以及 **Sandbox** 的平行擴展，我們為 Agent 創造了一個「輸得起、能試錯」的環境。這將 Agent 的表現從「隨機」推向了「確定性」。
*   **Context 是進化的靈魂：** 透過 **MemRL** 的雙階段檢索與 Q-value 動態更新，我們讓 Agent 具備了「吃一塹，長一智」的能力，這是在不觸動模型權重的前提下，實現持續學習 (Continual Learning) 的最優解。

### Traces 是唯一的真理

在這套架構中，不論是模組一、二還是三，它們的運作全部依賴同一個底層基礎設施：**結構化的執行日誌 (Structured Traces)**。

如果沒有完整的 Trace 記錄（包含：輸入、思考、工具調用、報錯、最終結果），你將無法：
1.  **離線做夢 (Dreaming)：** 無法總結高階規則。
2.  **熱路徑學習 (Hot-path)：** 無法更新 MemRL 的 Q-value。
3.  **Harness 優化：** 無法發現 Agent 在哪個環節鬼打牆。

**「先有觀測性 (Observability)，才有智能的進化。」** 這是每一位 Engineer 都必須銘記在心的格言。

### 行動清單

如果你今天要開始實作自己的 Agent，請遵循以下步驟，不要過早複雜化：

1.  **第一步：啟動你的 Ralph Loop**
    *   寫一個 300 行的 Python 腳本，用 `while(True)` 跑起你的 Agent。
    *   給它一個標準的 Sandbox 環境（甚至是本地的一個 Temp Dir）與一套 Bash 工具。
2.  **第二步：建置 Trace 收集系統**
    *   引入 LangSmith 或 Langfuse。確保每一次的工具調用回傳值（尤其是 Error）都被完整記錄。
    *   實作 **Head/Tail Log 截斷**，防止 Context 爆炸。
3.  **第三步：實作動態經驗庫 (MemRL Lite)**
    *   在你的 Vector DB 增加 `q_value` Metadata。
    *   手動寫入 10 個「成功的範例」與 10 個「失敗的反思」。
    *   在檢索時，引入簡單的加權分數 (\(Score = Sim + Q\))。
4.  **第四步：戴上「工程師帽子」進行迭代**
    *   盯著 Traces 看。如果 Agent 在同一個地方錯兩次，去修改 Harness 裡的 Tool 描述或 System Prompt。

### 結語：編程迴圈，而不是編程邏輯

未來的軟體開發，將會從「一磚一瓦寫 if-else」轉向「設計一套能自我進化的系統」。你不再是程式碼的創造者，你是 **「Ralph Loop 的編程者」** 與 **「經驗的策展人」**。

正如 Geoffrey Huntley 所言，這是一個「陶土拉胚」的過程。你的 Harness 越穩，你的 Context 越純淨，你的 Agent 就能在無限的循環中，逼近完美的解法。