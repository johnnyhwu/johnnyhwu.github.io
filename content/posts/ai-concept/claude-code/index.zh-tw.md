---
# weight: 1
title: "拆解 Claude Code：Agentic Loop、工具系統、Skills 與權限機制"
date: 2026-07-24
lastmod: 2026-07-24
draft: false
description: "從概念層拆解 Claude Code 的架構：read-think-act 的 Agentic Loop、工具系統、CLAUDE.md 專案記憶、Hooks、Skills、MCP，以及讓自主編碼 Agent 能安全運作的權限機制。"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Single-Agent", "Agent Memory"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1

url: "ai-concept/:contentbasename"
---

<!--more-->

## 前言

*   **它不是自動補全工具。** Claude Code 是 Anthropic 推出的 agentic 編碼 CLI：與其在人類主導下預測下一行程式碼，它更像是被交付一個目標後就自行主導全局——讀檔、下指令、改程式碼、驗證自己的成果，全部在一個迴圈中自主完成。
*   **「Model + Harness + Context」框架的具體實作。** [Harness Engineering](../harness-engineering/) 一文提出的「凍結模型、執行腳手架、動態組裝的 Context」三層架構並非只是理論——Claude Code 的工具系統、Hooks 與 `CLAUDE.md` 記憶,正是這套架構的實際落地。
*   **本文目標：** 走過 Claude Code 的核心機制——Agentic Loop、工具系統、擴充方式(Skills、Hooks、MCP)、Context 管理,以及讓自主編碼 Agent 能在無人看管下安全運行的權限機制。

## Claude Code 到底是什麼

Claude Code 以 CLI(以及 SDK)行程的形式運作,其核心其實只有一個原語:一個能呼叫工具、觀察結果、並決定下一步該做什麼的 LLM——如此反覆,直到它自己判斷任務已經完成。這裡沒有另外掛一個「規劃模組」或「執行模組」——規劃與執行都發生在同一個迴圈裡,由模型自己對剛才觀察到的結果進行推理來驅動。

這讓它與 IDE 的自動補全(預測 token,而非行動)以及早期「跟你的程式碼聊天」型助理(只能讀,無法動手)區隔開來。Claude Code 的關鍵特徵是:**觀察與行動使用同一套介質**——一次失敗測試的 stderr 會直接成為下一輪 prompt 的輸入,不需要人類居中轉達。

## Agentic Loop

這個迴圈說起來簡單,但要在正式環境中做對並不容易:

```python
def agent_loop(user_task, tools, cwd):
    context = load_project_memory(cwd)      # CLAUDE.md、先前的對話
    transcript = [user_task]

    while not done:
        response = model.call(transcript, context, tool_schemas=tools)

        if response.is_final_answer:
            done = True
            continue

        # 每一次工具呼叫,都是 harness 介入的機會
        if requires_confirmation(response.tool_call):
            approved = ask_user(response.tool_call)
            if not approved:
                transcript.append(denial_feedback(response.tool_call))
                continue

        result = execute(response.tool_call, cwd)
        transcript.append(observation(response.tool_call, result))
```

比起迴圈的外型,以下兩個特性更值得關注:

*   **每一輪都可被檢視。** 因為模型必須明確發出一個工具呼叫,而不是用自由文字說「我現在要去改檔案了」,harness 因此獲得一個乾淨的攔截點——可以在任何動作真正發生前,執行權限檢查、記錄 log、或觸發 Hooks。
*   **失敗只是另一種觀察結果。** 測試失敗、語法錯誤、被拒絕的權限請求——這些都不會讓迴圈中止,而是變成下一輪的輸入,模型會據此重新規劃。這與 [Ralph Loop](../harness-engineering/#ralph-loop-the-orchestrator) 「把它丟回轉盤上」的概念如出一轍:一個能從錯誤中恢復的單體迴圈,遠比一個沒有預期到錯誤會發生的脆弱多階段管線更穩健。

## 工具系統

Claude Code 的行動空間是一組精簡的通用工具,而非上百個針對特定任務打造的工具——這是刻意的設計,讓模型能夠自由組合工具,而不是四處尋找「剛好對的」那一個窄用途工具:

| 工具 | 角色 |
| :--- | :--- |
| `Read` / `Glob` / `Grep` | 理解程式碼庫——讀取已知檔案、依 pattern 找檔案、用正規表示式搜尋內容——不需要把整個專案塞進 context。 |
| `Edit` / `Write` | 進行有針對性的修改(`Edit` 是精確字串替換;`Write` 用於新檔案或整檔重寫)。 |
| `Bash` | 執行任意 shell 指令——build、test、lint、安裝套件、git——是專用工具涵蓋不到時的通用逃生門。 |
| `Task`(Subagent) | 把獨立、自包含的一段工作委派給另一個擁有自己 context window 的 Agent 實例,只回傳摘要結果。 |
| `WebFetch` / `WebSearch` | 當本地程式碼庫本身無法回答問題時,拉取檔案系統之外的資訊。 |

真正重要的設計選擇並非某一個特定工具,而是:凡是有專用、窄用途工具(`Read`、`Edit`、`Grep`)可用的地方,一律優先於通用的 `Bash` 逃生門。窄用途工具的失敗面遠比 shell out 到 `sed`/`cat` 小,其結構化輸出也更容易讓模型與 harness 雙方推理。

## 擴充 Agent:Skills、Hooks 與 MCP

一個凍結的模型加上固定的工具清單,對於編碼 Agent 實際會遇到的任務範圍來說仍然太過僵化。Claude Code 的 harness 層額外提供三個擴充點,各自解決不同的問題:

### Skills——封裝、可被發現的操作程序

Skill 是一個資料夾,裡面裝著描述如何完成特定、重複性任務的指示(可選附帶腳本)——本站自己用來把論文筆記轉成雙語部落格文章的 `hugo-paper-post` skill 就是一例。Skills 只會在需要時才載入 context:模型一開始只會看到每個可用 skill 的一行描述,只有真正用到的那一個,才會把完整指示拉進來。這正是 harness-engineering 筆記中 [Just-In-Time 工具注入](../harness-engineering/#just-in-time-jit-tool-injection) 所談的「漸進式揭露」原則——不該為當前任務用不到的能力預付 context 成本。

### Hooks——在生命週期節點上的確定性控制

Hooks 是 harness 在固定節點執行的 shell 指令——工具執行前、Agent 回覆完成後、Session 開始時。因為 Hook 是一般程式碼,而非模型呼叫,所以它是實作「模型本身無法被信任會可靠遵守」的保證的正確位置:阻擋對受保護路徑的寫入、在每次編輯後自動格式化檔案,或是在 lint 檢查不通過時直接讓該輪失敗。Hooks 讓「Agent 絕不能做 X」從系統提示裡一句寄望變成真正被強制執行的規則。

### MCP——連接外部世界的標準協定

Model Context Protocol 讓 Claude Code 能透過共通介面與外部服務對話——GitHub、資料庫、內部 API——而不必為每個整合手刻一套客製化工具程式碼。一個 MCP server 自己宣告它有哪些工具與資源;harness 再把這些工具以與內建工具相同的方式呈現給模型。這正是讓同一個 Agent 能同時觸及 Slack 工作區、工單系統與私有 repo,而 harness 作者不需要為每一個都自己寫一份 client 的關鍵。

## Context 工程的實務應用

Claude Code 同時也是 [Context Engineering](../context-engineering/) 筆記中諸多概念的實際案例——透過精心組裝 context,讓一個無狀態的模型「感覺」起來像有狀態一樣。

*   **`CLAUDE.md` 作為專案層級記憶。** 一份被 checked in 的 `CLAUDE.md`——就像管轄本 repo 部落格發文慣例的那一份——會在 session 開始時被讀取並自動摺入 context。它扮演的角色,正是 harness-engineering 筆記中「Org-level」記憶層:持久、共享,且不依附於任何單一對話。
*   **Context 壓縮(Compaction)。** 長時間的 session 終究會逼近 context window 的上限。Claude Code 不會盲目截斷,而是把較早的對話摘要成精簡版本後繼續工作——對話得以延續,使用者不需要重啟或重新解釋先前的決策。
*   **Subagent 作為 Context 隔離手段。** 透過 `Task` 工具把一次範圍廣、探索性的搜尋(例如「找出某個設定值在大型程式碼庫裡所有被用到的地方」)派給 Subagent,能讓這次搜尋雜訊多的中間輸出留在主迴圈的 context 之外——只有 Subagent 最終的摘要會回傳。這正是 Context Engineering 筆記中「Folding」模式的實際應用:複雜的子任務讓 context 長度呈現鋸齒狀變化,而不是對主對話造成永久性、不斷累積的負擔。

{{< admonition tip "為什麼這件事在實務上很重要" >}}
這三個機制單獨拿出來看都不算新穎——摘要、範圍化委派、專案設定檔,在 agentic 編碼工具出現之前就已存在。真正讓它們成為「Harness」而非單純「功能」的,是它們能自動彼此組合:Subagent 的摘要本身也可能在後續的壓縮流程中被再次摺入,而 `CLAUDE.md` 的慣例無論當前這一輪來自使用者、或來自 Hook 觸發的重試,都會被一致地套用。
{{< /admonition >}}

## 權限機制與影響範圍(Blast Radius)

一個能無人看管地執行任意 shell 指令、修改檔案的 Agent,需要一層不能單純仰賴模型「每次都猜對」的安全機制。Claude Code 的做法是漸進式的,而非二元的:

*   **權限模式(Permission Modes)** 從「每個非瑣碎動作都先詢問」,到「在明確清單內自動核准」(例如唯讀指令,或工作目錄內的編輯),再到「在隔離環境中完全自主執行」——由使用者選擇模式,而非模型自己決定。
*   **可逆性決定是否需要確認提示。** 讀取檔案或執行測試在幾乎所有模式下都會被自動核准,因為就算判斷錯了,代價也很低。強制推送(force-push)、刪除分支、`rm -rf` 這類動作,在任何模式下預設都需要明確確認,因為事後可能根本無法復原。
*   **沙盒限制了最壞情況的範圍。** 即使在寬鬆的模式下,在容器或範圍受限的環境中執行,也代表一個錯誤的 shell 指令無法觸及任務工作目錄以外的地方——權限機制與執行邊界是兩道獨立的防線,而非互相替代。

這與 harness-engineering 筆記中 [Git-based State & Sandboxes](../harness-engineering/#git-based-state--sandboxes) 一節的討論如出一轍:目標不是讓 Agent 完全不可能犯錯,而是讓犯錯的代價變得低廉且可逆,使迴圈得以持續運作,而不需要人類在每一次失誤時都出手介入。

## Claude Code 在 Agent Harness 版圖中的定位

相較於 [OpenClaw](../openclaw-intro/) 強調長時間運行的自主性與自製工具能力,Claude Code 的定位刻意較為聚焦:它主要針對軟體工程的迴圈本身做優化——讀程式碼、改程式碼、驗證變更——並以 Skills、Hooks 與 MCP 作為把這個迴圈延伸到鄰近任務(包括撰寫這篇文章本身)的機制,而非追求開放式的一般性自主。這是刻意的取捨:一個範圍較窄、觀測性良好的行動空間,比起完全通用的行動空間,更容易同時做到「有能力」與「安全」。

## 結語

與其把 Claude Code 理解成「一個能存取檔案的聊天機器人」,不如把它看作圍繞著一個凍結模型所建構的精簡、可組合的 Harness:一個緊湊的 Agentic Loop、一組刻意精簡的工具系統、三個在不膨脹基礎 context 的前提下擴充能力的機制(Skills、Hooks、MCP),以及一套讓確認的摩擦力隨動作可逆程度而調整的權限機制。這些單獨拿出來看都不算是什麼特殊技術——真正讓它能運作的,是這些機制被設計成可以彼此組合:幾天前開始的 session、專案自己的慣例,以及一次性委派出去的子任務,最終都能乾淨地回饋到同一個迴圈裡。
