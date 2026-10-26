---
# weight: 1
title: "WikiSkill 解析：把執行紀錄編譯成 wiki，skill 才越改越準"
date: 2026-09-02
lastmod: 2026-10-27
draft: false
description: "agent skill 自動演化每輪都要從原始執行紀錄重新分析。WikiSkill 在紀錄與 skill 之間加一層不會被回滾的 wiki：五個模型全面領先，消融實驗多出 15.0 分，但最想證明的「結構化勝過扁平清單」其實沒被直接驗證。"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## skill 自動演化的老毛病：分析過的失敗，下一輪又從頭分析

讓 agent 自己改自己的 skill（把某個領域的操作步驟寫成一份文件，讓 agent 執行任務時讀來套用；例如一份 skill 可能寫著「發現自己一直在拿起又放下同一個東西時，先檢查任務是不是已經完成」），聽起來很美：跑一批任務、看哪裡錯、改 skill、驗證有進步才留下。做過的人大概都遇到同一件事：每一輪都得從原始的執行紀錄（trace，agent 每次做任務留下的完整過程）重新爬一次失敗原因，前幾輪分析出來的東西沒有被好好留下來。

現有方法也有某種「記憶」，但頂多是一份「提案歷史清單」，附掛在 skill 的修改紀錄旁邊，算不上一個真正被維護的知識庫。

Google Research 跟 Virginia Tech 這篇 *WikiSkill* 論文（arXiv:2608.27454，2026 年 8 月）想解的就是這件事：在「原始執行紀錄」跟「最終的 skill 文件」之間，插入一層**持久的知識層**，也就是 wiki，一組被整理過的結構化筆記；WikiSkill 的 Wiki 指的就是這一層。它不會因為某次提案被拒絕就被回滾（回滾，就是把這一輪的修改整組退回上一版），讓每一輪的 skill 修改都能站在累積的證據上做判斷，而不是每次從零分析。這個構想不是原創：作者自己在論文開頭就講明，是受 Andrej Karpathy 一篇談「LLM Wiki」的 gist（一篇公開的短文）啟發。但論文把它系統化實作，並在 5 個模型、5 個任務上紮實驗證。

{{< admonition abstract "先講結論" >}}
WikiSkill 在五個模型上的平均分數都最高。最紮實的證據來自一組消融實驗（逐一拿掉系統的某個部分，看分數掉多少，藉此判斷每個部分的貢獻；只在 Gemini-3.5-Flash 上做）：只把負責提出 skill 修改的角色（Skill Proposer）接上 wiki，平均分數就從 48.7% 升到 63.7%，多了 15.0 分。

但論文最想主張的那件事，「結構化整理過的 wiki 比扁平的歷史列表更好」，沒有對應的對照組直接驗證，只能算作者的主張。
{{< /admonition >}}

路線是這樣：先看現有方法的記憶缺了什麼，再看 WikiSkill 的三層架構、四個角色和一個完整案例；接著看主實驗和消融實驗各證明了什麼、哪裡留下缺口；最後談工程成本，和可以帶走的判斷。

## 問題：現有方法的記憶只是附在修改紀錄旁的扁平清單

Agent skill 是一種輕量級的知識封裝方式：把特定領域的操作步驟打包成一個獨立的檔案目錄，核心是一份 `SKILL.md`，讓 agent 執行任務時可以讀取套用，不需要重新訓練模型參數。手動寫這些 skill 很花人力，於是最近一批研究開始讓 agent 自動演化 skill：先跑一批訓練任務，分析成功與失敗的執行紀錄，再據此修改 skill 內容，如此反覆迭代。

論文拿來比較的三個代表方法，EvoSkill、Trace2Skill、[SkillOpt](../skillopt/)，都遵循同一套流程：跑任務、分析 trace、修改 skill、驗證後決定是否採用（在另外留出來、不拿去訓練的一組任務，也就是驗證集上測試新版 skill）。它們也都有某種形式的「記憶」，例如 EvoSkill 會保留一份跨迭代不清空的提案與評估結果清單。但論文點出一個共同弱點：這些記憶都是附屬在「skill 修改紀錄」本身上面的**扁平清單**，沒有被當成一個獨立、會持續整理、隨時間增厚的知識表示法來維護。

WikiSkill 的看法是：缺口不在「有沒有記憶」，而在記憶只是被動堆在旁邊的一份清單，所以要補的是一個會被主動整理、持續增厚的知識層。

## 做法：在原始紀錄和 skill 之間插一層不回滾的 wiki

WikiSkill 的答案是多一層。下面先看三層各自的角色，再看一輪迭代裡四個角色怎麼接力，接著釐清三個最容易搞錯的規則，最後用一個真實案例（上面那種「一直拿起又放下」的循環，真的在實驗裡出現過）走一遍。

### 三層各管什麼，誰能改、誰會被整組退回

WikiSkill 把 agent 的工作空間切成三層，每一層的改法規則都不一樣：

| 層 | 特性 | 內容 |
| --- | --- | --- |
| Skill Layer（`skills/`） | 可逆、有條件更新 | 實際會被注入 prompt 的技能文件 |
| Wiki Layer（`wiki/`） | 持續累積、絕不重置 | 整理過的結構化知識 |
| Raw Layer（`raw/`） | 永久保存、只能新增 | 原始執行軌跡 |

可以把這三層想成一個調查案件：Raw 是監視器錄影，只會越存越多；Wiki 是調查員邊看邊整理的案件筆記，不會因為某一版作業手冊被打回就丟掉；Skill 是最後發出去的作業手冊，可以整本退回上一版。

Wiki Layer 是這篇論文新加的中間層，裡面有三種檔案：

- `patterns/`：底下一堆 markdown 檔，一個檔案對應一個具體的失敗模式或成功策略。
- `logs.md`：按時間順序記錄每次迭代做了什麼。
- `skill-impact.md`：記錄每次提案內容、驗證分數、被接受或拒絕的結果。

Skill Layer 每個 skill 資料夾則有兩個檔案：`SKILL.md` 是技能內容本身，`PURPOSE.md` 記錄這個技能是被 wiki 裡哪些 pattern 啟發、修改過的動機。

### 一輪迭代裡，四個角色怎麼接力

三層是靜態的空間結構，實際運作靠四個角色依序互動，跑完一次迭代：

1. **Inference Agent** 用上一輪的 skill 集合跑訓練任務，結果寫入 Raw Layer（只能新增，不能存取 wiki）。
2. **Wiki Maintainer** 用一次 LLM 呼叫，抽樣少量 trace 做根因分析（找出失敗背後真正的原因，而不只看表面症狀），更新 wiki 的 pattern、index（一份列出各 pattern 摘要的目錄）、log。
3. **Skill Proposer** 以多輪 ReAct（交替進行推理與工具呼叫）agent 的方式，依序讀 wiki index、`skill-impact.md`、相關 pattern、原始 trace，提出一個 skill 的新建或修改（一次只改一個）。
4. **Gating & Rollback** 在驗證集上測試候選 skill，分數進步就採用，沒進步就整組退回上一版，不論結果都把提案內容、diff、分數寫進 `skill-impact.md`，再進入下一輪。

{{< image src="figure2.png" alt="WikiSkill 框架示意圖：最底層是不可變的原始執行紀錄，中間是持續累積的 Wiki 知識層，最上層是實際會被注入 prompt 的 Skill 層，四個角色依序互動完成一次迭代。" caption="圖 1 — WikiSkill 框架總覽：Raw / Wiki / Skill 三層架構，以及一次迭代裡四個角色的互動順序。（來源：原始論文 Figure 2。）" >}}

這裡有個關鍵設計：**Inference Agent 在跑訓練任務時完全不能存取 wiki**。這個限制在後面的消融實驗裡被驗證是必要的：如果讓它偷看 wiki，反而會讓最終 skill 品質變差，原因留到後面講。

{{< fold title="Wiki Maintainer 的 prompt 長什麼樣：index 的品質和 pattern 一樣重要" tone="info" >}}
論文附錄提供了 Wiki Maintainer 完整的 system prompt。角色定義要求它對執行紀錄做深度根因分析，不能只看表面症狀；輸入是這輪的原始 trace 加上目前的 wiki context；輸出固定成 JSON，包含新建 pattern、對既有 pattern 的修改、完整更新後的 index 內容（不是差異）、這輪迭代的摘要。

其中有一段標注為 CRITICAL 的指示特別值得注意：`index.md` 的條目是 wiki 裡最重要的部分，因為它們決定了 inference agent 會不會去讀完整的 pattern 頁面，描述必須具體到讓 agent 不用讀完整頁面就能判斷相關性，同時包含問題、根因跟解法。這透露一個工程細節：pattern 頁面寫得再好，如果 index 摘要品質差，後面的 agent 根本不會點進去看，所以 index 品質被拉到跟 pattern 內容本身同等地位。
{{< /fold >}}

### 三個最容易搞錯的規則：誰能刪、誰能改、誰只能加

討論這類分層設計時，最容易產生誤解的，是「哪一層能刪、能改、只能加」。實際規則跟直覺不太一樣：

- **Skill Layer 沒有「刪除」這個操作。** Skill Proposer 的輸出格式只有新建、修改既有、不動作三種，沒有刪除。你以為的「刪除」其實是 Gating & Rollback 造成的整組版本回退：新提案沒通過驗證，系統直接把整個 skill 集合退回上一輪版本，不是針對單一 skill 做刪除。
- **Wiki Layer 不是只能新增。** Wiki Maintainer 對既有 pattern 頁面有三種修改方式：在檔案尾端加、找到指定文字替換、在指定文字後插入。所以既有內容可以被修正、覆寫。「永不重置」講的是整個 wiki 狀態不會因為某次提案被拒絕而回滾，不是「每個檔案只能加不能改」。
- **Raw Layer 的唯讀，是「使用方式」的唯讀。** 這層每輪迭代都會新增這輪的執行紀錄，持續增長，「immutable」指的是已寫入的紀錄不會被修改或覆蓋。Wiki Maintainer 跟 Skill Proposer 對它的存取確實是唯讀，但這層本身一直在長大。

### 走一遍：一個 skill 怎麼被 wiki 一步步塑造出來

這個案例具體示範前面講的機制實際長什麼樣：場景是 ALFWorld（論文用的五個任務之一，要 agent 在模擬環境裡實際操作物品的具身互動任務）上，Qwen-3.6-27B 演化出一個叫 `break-repetition-loop` 的 skill 的完整過程。

{{< image src="figure3.png" alt="時間軸示意圖：第 0 輪 Wiki Maintainer 建立 pattern 頁面、Skill Proposer 提案被拒絕；第 1 輪根據拒絕紀錄提出更聚焦的新提案並被接受；之後幾輪持續有新證據疊加進同一個 pattern 頁面，並在第 4 輪據此修改該 skill。" caption="圖 2 — Wiki 引導 skill 演化的案例研究（ALFWorld，Qwen-3.6-27B）。（來源：原始論文 Figure 3。）" >}}

**第 0 輪。** Wiki Maintainer 建立了一個 pattern 頁面 `take-examine-move-loop.md`，描述 agent 會拿起物品、檢查、放回原位、不斷重複這個循環，證據來自兩筆訓練資料。同一輪，Skill Proposer 提案新建一個叫 `goal-directed-action` 的 skill，但驗證分數 0.72，沒超過 baseline（目前要超越的最佳分數），被拒絕。`skill-impact.md` 完整記下了這次的 diff（修改前後的差異）跟拒絕結果。

**第 1 輪。** Wiki Maintainer 發現同樣的錯誤又出現了，還多了一個新變體，於是把新證據追加進既有的 pattern 頁面。Skill Proposer 這次讀到了第 0 輪的拒絕紀錄，提案改成新建一個更具體、更聚焦動作模式的 skill `break-repetition-loop`，驗證分數 0.78，通過。

**第 2 到第 4 輪。** 第 2 到第 3 輪（論文沒有展開），Wiki Maintainer 又建立了一個新 pattern `multi-operation-loop.md`，描述 agent 對同一物品重複做操作卻不檢查任務是否已完成。到了第 4 輪，Skill Proposer 讀到這個新證據，提案修改（不是重建）`break-repetition-loop`，再次通過。

最終這個 skill 的 `PURPOSE.md` 只用一行話就交代清楚了來龍去脈：「建立為 break-repetition-loop。前一次嘗試 goal-directed-action 因為太抽象而被拒絕。這一版更精簡，用的是具體的動作模式。」不用回頭爬原始 trace 自己猜，光看這一行就知道這版 skill 為什麼長這樣。而「每種操作類型只做一次」這條規則能在第 4 輪被加進去，正是因為對應的 pattern 頁面持續累積了跨迭代證據。後面會看到的消融實驗裡，「Skill Proposer 有 wiki 存取權帶來 +15 分」，這個案例就是它的一個具體實例。

記住這個案例的形狀：第 0 輪被拒絕的提案沒有白費，它變成第 1 輪更聚焦的依據；之後新的失敗證據不斷疊進 pattern 頁面，第 4 輪才有了修改 skill 的理由。三層分工的好處，就是讓這條線索不會斷。

## 實驗結果：五個模型都領先，但領先幅度差很多

看完機制，來看它在實驗裡表現如何：先看主結果有多穩，再看效益怎麼隨模型規模變，最後看一個模型演化出的 skill 能不能搬給另一個模型用。

### 主結果：穩定，不只是峰值高

實驗涵蓋 5 個模型（Qwen-3.5-4B、Qwen-3.5-9B、Qwen-3.6-27B、Gemma-4-31B、Gemini-3.5-Flash）乘上 5 個任務：數學推理 LiveMath、需要 web search 的事實問答 SealQA、試算表操作 SpreadSheet、長文件問答 OfficeQA、具身互動任務 ALFWorld。每個任務都是一套 benchmark（拿來比較模型表現的標準測試題），每個組合跑三次完整演化流程取平均。

{{< image src="figure1.png" alt="長條圖顯示五個模型在無 skill、以及 EvoSkill、SkillOpt、WikiSkill 三種演化方法下的平均準確率，WikiSkill 全面領先，且模型越大領先幅度越明顯。" caption="圖 3 — 五個模型的平均表現對照：WikiSkill 在所有模型上都領先，且優勢隨模型能力增強而放大。（來源：原始論文 Figure 1。）" >}}

核心數字是：WikiSkill 在全部 5 個模型上平均分數都最高，跟每個模型「表現最好的競爭對手」相比，領先的幅度如下：

| 模型 | 領先最強對手的百分點（對手 = 該模型上表現最好的競爭方法） |
| --- | --- |
| Qwen-3.5-4B | 3.3 |
| Qwen-3.5-9B | 5.1 |
| Qwen-3.6-27B | 10.0 |
| Gemma-4-31B | 5.8 |
| Gemini-3.5-Flash | 12.0 |

幾個較顯眼的單點例子：Gemini-3.5-Flash 在 LiveMath 上從 33.0% 拉到 72.6%，在 SpreadSheet 上從 50.5% 拉到 76.6%；Qwen-3.6-27B 在 ALFWorld 上從 52.8% 拉到 77.6%。

{{< image src="table1.png" alt="表格顯示五個模型分別在無 skill、以及 EvoSkill、Trace2Skill、SkillOpt、WikiSkill 四種方法下，於五個任務上的準確率對照。" caption="表 1 — 跨模型、跨任務的主要結果對照表。WikiSkill 在每個模型區塊的平均分數都是最高。（來源：原始論文 Table 1。）" >}}

論文特別強調的是**穩定性**，不只是峰值表現。其他方法在部分設定上會明顯退步，不是單純進步較少而已：EvoSkill 讓 Qwen-3.5-9B 在 LiveMath 上大幅進步（28.2%→58.1%），卻讓 Gemma-4-31B 在同一任務上退步（33.9%→29.8%）；SkillOpt 讓 Gemini-3.5-Flash 在 SealQA 上退步（29.4%→28.2%）。WikiSkill 沒有出現這種時好時壞的情況。

{{< admonition note "Gemini 在 ALFWorld 的 85.9% 不代表沒效果" >}}
Gemini-3.5-Flash 在 ALFWorld 上，所有方法（含無 skill）的分數都是 85.9%。原因是它在演化開始前，驗證集就已經拿到 100% 分數，觸發了提早終止機制，根本沒真的跑演化流程。不是 WikiSkill 在這個任務上沒效果，是這個任務對它來說本來就太簡單。
{{< /admonition >}}

### 模型越大，skill 演化的收益越大

論文用「skill evolution 跟 model scaling **互補**」來描述這個發現。在 Qwen 系列裡看得最清楚（同一家族只有參數量不同，比較乾淨）：WikiSkill 帶來的平均進步幅度（和沒用 skill 的同一個模型相比）隨規模遞增；在 SpreadSheet 這個任務上尤其明顯。

| 模型 | 比沒用 skill 的平均進步 | SpreadSheet 上比沒用 skill 的進步 |
| --- | --- | --- |
| Qwen-3.5-4B | +12.3 分 | +6.5 分 |
| Qwen-3.5-9B | +17.5 分 | +9.3 分 |
| Qwen-3.6-27B | +23.9 分 | +40.9 分 |

一個更直覺的說法是：小模型加上好的 skill，可以反過來打贏沒有 skill 的大模型。Qwen-3.5-9B 加上 WikiSkill，平均準確率拿到 47.4%，超過 Qwen-3.6-27B 完全沒用 skill 時的 39.4%。論文的解讀是：模型能力跟演化出的程序性知識（怎麼一步步做事的知識），提供的是互補的效能來源。越強的模型越能有效開發跟執行更精細的 skill，獲益也就越多；而有效的 skill，則可以讓小模型彌補跟大模型之間的能力差距。

不過跨資料集的效益也不平均。Qwen-3.6-27B 在 OfficeQA（長文件檢索型任務）只進步 11.6 分，相較之下在 SpreadSheet 上進步 40.9 分。論文沒有針對這個模型自己內部的落差再進一步拆解，但對 OfficeQA 這類任務有一個相關的觀察：大模型能有效運用演化出的搜尋流程導覽長文件，小模型（如 Qwen-3.5-4B）卻沒辦法執行這種多步驟搜尋流程，反而退回預設閱讀行為，導致些微退步。這點跟下一節的跨模型遷移結果互相呼應。

### 跨模型遷移：能不能搬走，看 skill 裡包的是什麼

這一組實驗在測：用模型 A 演化出來的 skill，能不能直接拿給模型 B 用？

{{< image src="table2.png" alt="表格顯示用無 skill、以及 Qwen-3.5-4B、Qwen-3.6-27B、Gemini-3.5-Flash 三個來源模型演化出的 skill，分別套用到各個推論模型上的準確率對照。" caption="表 2 — 跨模型 skill 遷移結果。灰底列是模型自己演化、自己使用的情況。（來源：原始論文 Table 2。）" >}}

三個發現值得拆開來看：

| 發現 | 具體例子 |
| --- | --- |
| 遷移過去的 skill，常常比自己演化的還好用 | Qwen-3.6-27B 的 skill 拿給 Qwen-3.5-9B 用在 SpreadSheet 上，拿到 50.5%，比它自己演化的 skill（33.6%）還高 |
| 能不能遷移，取決於 skill 包的是通用程序還是模型專屬的權宜之計 | LiveMath 的 skill 遷移得特別好（33.0%→67-74%）；但 SpreadSheet 上，Qwen-3.5-4B 的 skill 拿給 Gemini-3.5-Flash 用，分數從 50.5% 掉到 18.1%，同樣情境換成 Qwen-3.6-27B 的 skill 卻拉到 63.4% |
| 即使 skill 來源相同，不同接收模型「消化」skill 的能力也不一樣 | Qwen-3.5-4B 自己演化的 skill 拿給自己用反而退步（30.2%→28.5%），同一份 skill 拿給 Qwen-3.6-27B 用卻進步（42.1%→52.9%） |

第二點的負遷移案例，論文有做根因分析：小模型演化出的 skill 包了很多低階權宜之計（例如單行 Python 指令、字串轉換規則），幫小模型避開執行失敗，卻反而限制了強模型使用更完整的端到端腳本；破碎化的診斷流程也會製造多餘工具呼叫，可能在任務完成前就耗光強模型的互動預算。

{{< admonition note "論文沒有解釋的一個現象" >}}
但論文**沒有**解釋另一個更反直覺的現象：小模型（Qwen-3.5-4B）演化出的 skill，拿給 Gemma-4-31B 用之後，在 LiveMath、ALFWorld 上都讓它變好（分別拉到 73.1%、66.9%）。這件事論文只報告了數字，沒有進一步的根因分析。

整體來看，論文給了很多「哪個方向遷移得好或不好」的現象描述，但真正做因果解釋的只有 SpreadSheet 這一個案例，而且做的也只是定性的錯誤分析，不是系統性驗證。
{{< /admonition >}}

把上面三個發現合起來看，論文提出一個值得記住的框架性論點：自我演化這件事，其實混雜了兩種不同的能力，「從經驗中發掘出有用的程序性知識」跟「在推論時有效執行這些知識」。這兩者是可以拆開來看待的獨立能力，不是同一件事。這個視角比論文本身更通用：評估任何「self-improving agent」系統時，都可以先問一句，這個系統進步了，是因為它學到更好的東西，還是因為它更會照著指示做？

所以實驗這一段讀下來：領先是穩的，幅度隨模型變強而放大；但一份 skill 能不能搬走，要看裡面包的是通用的程序，還是只替來源模型補洞的權宜之計，接收的模型消不消化得了也是另一個變數。

## 消融實驗：wiki 到底在哪裡起作用

接下來是整篇論文實驗設計最乾淨的一組：它回答的是「有沒有 wiki 差多少」，以及 wiki 到底是在哪個環節起作用。

### 給 Skill Proposer 看 wiki 多 15.0 分，給訓練時的 agent 看反而扣分

這組只用 Gemini-3.5-Flash 一個模型做，分別調整 Inference Agent 跟 Skill Proposer 是否有 wiki 存取權。

要注意的是，只要 Skill Proposer 沒有 wiki 存取權，負責維護 wiki 的 Wiki Maintainer 這個角色也就一併移除了。下面四種消融設定，加上完全不跑 skill 演化的基準線，一共五個數字：

| Inference Agent 有 Wiki？ | Skill Proposer 有 Wiki？ | 平均分數 | 備註 |
| --- | --- | --- | --- |
| — | — | 40.4% | 無 skill 基準線 |
| 有 | 無 | 45.3% | Wiki Maintainer 已移除 |
| 無 | 無 | 48.7% | Wiki Maintainer 已移除 |
| 有 | 有 | 60.9% | 完整配置 |
| 無 | 有 | 63.7% | **WikiSkill 預設配置** |

{{< image src="table3.png" alt="表格顯示四種消融設定下（Inference Agent 有無 wiki 存取、Skill Proposer 有無 wiki 存取）的五個 benchmark 平均分數。" caption="表 3 — 消融實驗結果：分別關閉 Inference Agent、Skill Proposer 的 wiki 存取權，觀察平均分數變化。（來源：原始論文 Table 3。）" >}}

**第一個結論：讓 Skill Proposer 存取持久 wiki，效果非常顯著。** 在 Inference Agent 不能碰 wiki 的前提下，單純把 Skill Proposer 的 wiki 存取權打開，平均分數從 48.7% 跳到 63.7%，足足 +15.0 個百分點，是整篇論文裡最大幅度的單一變因效果。細看子項，LiveMath 從 51.3% 拉到 72.6%，SpreadSheet 從 49.9% 拉到 76.6%。論文的解釋是：沒有跨迭代累積的知識，Skill Proposer 很難處理複雜、需要多次迭代才能收斂的失敗模式。

**第二個結論：讓 Inference Agent 訓練時也碰 wiki，反而讓最終 skill 品質變差。** 在 Skill Proposer 已經有 wiki 存取權的前提下，如果連 Inference Agent 訓練時也讓它看 wiki，平均分數從 63.7% 掉到 60.9%，LiveMath 掉最多（72.6%→64.8%）。這也是為什麼架構設計裡刻意規定 Inference Agent 訓練時不能看 wiki。

{{< admonition info "論文對這個退步的解釋（只是假設）" >}}
當 Inference Agent 訓練時同時能看到 skill 跟 wiki，它可能直接從 wiki 裡找答案來解題，而不是靠 skill 本身解題。這樣一來產生出來的訓練 trace 就會失真：agent 表現好不是因為 skill 好用，是因為 wiki 幫了忙，這會讓 Skill Proposer 拿到的訓練訊號失去代表性。

論文明確把這標注為一個假設，沒有進一步驗證。
{{< /admonition >}}

### 最想證明的主張，正好是消融沒測到的那一塊

表面上看，EvoSkill 也維護了一份跨迭代不清空的提案歷史，那 WikiSkill 到底多做了什麼？答案不是「有沒有記憶」，而是**記憶的形式**：

|  | EvoSkill 的歷史列表 | WikiSkill 的 wiki |
| --- | --- | --- |
| 儲存形式 | 扁平列表：一筆一筆的提案內容、驗證分數、接受或拒絕 | 結構化、按主題組織的知識頁面，每頁對應一個具體的失敗模式或成功策略 |
| 有沒有獨立的整理步驟 | 沒有，proposer 自己看歷史列表加這次的原始 trace，現場消化 | 有專門的 Wiki Maintainer，職責就是做根因分析、把原始 trace 提煉合併進既有 pattern 頁面 |
| 證據累積方式 | 每次的失敗案例基本上獨立存在 | 同一個 pattern 頁面會跨迭代持續疊加證據 |
| 能不能查找相關知識 | 沒有索引機制，只能整份歷史從頭看 | 有 `index.md`，每個 pattern 一行摘要（問題、根因、解法），讓 proposer 快速判斷哪些知識相關 |

濃縮成一句話，這就是 WikiSkill 的核心主張：**知識需要被主動整理、消化、累積證據，而不只是被動地按時間堆疊。**

{{< admonition warning "消融實驗設計上的缺口" >}}
表 3 拿掉 wiki 的那組設定，是完全移除 Wiki Maintainer，測的是「有結構化知識」對比「完全沒有跨迭代知識」，並沒有設計一組對照組去比較「結構化 wiki」對比「像 EvoSkill 那樣的扁平歷史列表」。換句話說，表 3 證明了「有結構化知識 > 完全沒有知識」（+15%），但沒有直接證明這篇論文最想主張的那件事：「結構化知識 > 扁平列表知識」。

表 1 雖然有跟 EvoSkill 整體比較分數，但那個比較混雜了另一個變因：WikiSkill 的 Skill Proposer 是可以動態探索 10 到 20 輪的多輪 ReAct agent，而 EvoSkill 沒有這種機制，沒辦法乾淨歸因到「wiki 的結構化程度」這一項上。這是整篇論文論證上最大的一個缺口。
{{< /admonition >}}

所以消融這一段要分開讀：「有 wiki 比沒有 wiki 好」在 Gemini-3.5-Flash 上證得很紮實；但「為什麼要整理成結構化的頁面」，是作者的主張，不是這組實驗量到的結果。

## 工程面：廣度、深度與呼叫成本

最後補兩個工程面的問題：資料量大時，分析要怎麼分批；以及呼叫次數少，是不是就代表便宜。

### 為什麼訓練跑全資料集，分析卻只精讀一小部分

這一節回答一個實際問題：訓練資料變多時，分析的工作量怎麼不跟著暴增？答案分兩步：先把分析的批次設成整個訓練集，讓每輪只分析一次；再把「看得廣」和「看得深」拆開處理，讓這一次分析讀得進去。

論文附錄定義的 batch size 這個參數，常常讓人搞混它管的到底是什麼。要拆成兩層看才清楚：Inference Agent 每輪迭代一定對整個訓練集跑一次 rollout（讓 agent 實際把任務做一遍），這件事跟 batch size 無關；batch size 真正控制的是「分析加提案」這個步驟要分幾次做。如果 batch size 小於訓練集大小（EvoSkill、SkillOpt 用的方式），訓練集會被切成多個小批次，各自觸發一輪完整分析；WikiSkill 則把 batch size 設成等於訓練集大小，所以每輪迭代只做一次分析。

|  | 廣度 | 深度 |
| --- | --- | --- |
| 目的 | 避免只看到部分資料而誤判某個錯誤模式的普遍性 | 控制成本，應付 context window（模型一次能讀進去的長度上限）的限制 |
| 做法 | 全批次 rollout，加上 Skill Proposer 一開始拿到的全部任務成敗摘要 | 有限抽樣：Wiki Maintainer 是單次呼叫、固定抽樣；Skill Proposer 是多輪 ReAct、動態按需讀取 |
| 具體規則 | （看全部） | Wiki Maintainer 每輪固定抽樣最多 8 筆（5 敗 3 成），每筆截斷到 15,000 字元；Skill Proposer 不受這個限制，可以自己動態挑選整個訓練集的 trace 精讀，規則只要求至少讀滿 4 筆，沒有上限 |

所以每輪只分析一次（batch size 設成整個訓練集）；廣度靠全批次，深度靠抽樣，讓這一次分析讀得進 context window。

### 呼叫次數固定，不等於總成本低

這裡算的是「每輪迭代，分析加提案這個步驟本身要打幾次 LLM API」，不含 Inference Agent 本身跑訓練任務的呼叫。

WikiSkill 每輪迭代的呼叫次數是 \( 1 + T_{\text{ReAct}} \)，其中 \( T_{\text{ReAct}} \) 是 Skill Proposer 用掉的 ReAct 輪數，在論文實驗裡大約落在 10 到 20 之間。會化簡成這樣，是因為論文全部資料集都把 batch size \( B \) 設成等於訓練任務數 \( N_{\text{train}} \)，\( N_{\text{train}} / B \) 恆等於 1。結果是呼叫次數只跟 ReAct 輪數有關，跟訓練集大小完全無關。

這代表訓練集從 80 筆變成 800 筆，WikiSkill 每輪迭代的呼叫次數不會變，但 EvoSkill、SkillOpt 都是批次越小、資料越多，呼叫次數線性增加；Trace2Skill 更明確，因為它規定每一筆 trace 都要單獨分析一次，不管怎麼調 batch size，呼叫次數下界永遠跟訓練集大小成正比，是四者裡複雜度最差的。

{{< admonition warning "呼叫次數少，不等於總成本低" >}}
論文自己也承認這個「呼叫次數固定」的代價：每一輪 ReAct 都是一次完整的 LLM 呼叫，而且 Skill Proposer 讀的 context 通常比單筆 trace 分析要大很多。

換句話說，呼叫次數少不等於總 token 成本低：如果每一輪 ReAct 都在讀很長的 wiki context 加 trace 內容，單次呼叫的 token 用量可能遠超過 EvoSkill 那種「小批次、多次但每次讀得少」的呼叫方式。論文完全沒有提供 token 層級的成本比較，只比較了呼叫次數這一個指標，這是評估這套框架實際部署成本時容易被忽略的陷阱。
{{< /admonition >}}

{{< fold title="四個框架的完整公式，和論文原表" tone="info" >}}
| 方法 | 每輪迭代的呼叫次數 |
| --- | --- |
| WikiSkill | \( (1 + T_{\text{ReAct}}) \times (N_{\text{train}} / B) \) |
| EvoSkill | \( 2 \times N_{\text{train}} / B \) |
| SkillOpt | \( K_{\text{opt}} \times N_{\text{train}} / B \) |
| Trace2Skill | 大約 \( N_{\text{train}} + (1 + 1/(c-1)) \times (N_{\text{train}} / B) + 1 \) |

\( N_{\text{train}} \) 是訓練任務的數量，\( B \) 是 batch size，\( T_{\text{ReAct}} \) 是 Skill Proposer 的 ReAct 輪數。\( K_{\text{opt}} \) 與 \( c \) 的定義請見論文原表，本文不重述。

{{< image src="table7.png" alt="表格列出 WikiSkill、EvoSkill、SkillOpt、Trace2Skill 四種框架每輪迭代的 optimizer API 呼叫次數公式與複雜度等級對照。" caption="表 4 — 四種 self-improving agent 框架的 optimizer API 呼叫複雜度對照。（來源：原始論文 Table 7。）" >}}
{{< /fold >}}

## 帶走：證據的三個等級，和四個通用判斷

回頭整理：三件事，各自證得的程度不同；再加上四個脫離這篇論文也用得上的判斷。

### 證得多紮實，限制在哪

論文的核心貢獻本身不算原創，作者自己講明是把 Karpathy 的 LLM Wiki 構想套用到 skill evolution 上。這篇論文真正做的事，是把這個構想系統化實作，並在 5 個模型、5 個任務上紮實驗證，做出了整篇論文裡唯一算乾淨的消融實驗。三件事證得程度不一：

| 證得程度 | 內容 |
| --- | --- |
| 最紮實 | 給 Skill Proposer 一個持久、不隨 gating 結果回滾的知識層，效果遠好於完全沒有跨迭代知識（消融實驗只在 Gemini-3.5-Flash 上做） |
| 中等 | 效益隨模型規模遞增、發掘知識與執行知識可以拆分，但部分現象（例如小模型的 skill 讓大模型變好）沒有因果解釋 |
| 沒有被證明 | 「結構化整理過的知識」比「扁平歷史列表」更好，這只是論文自己的主張，也是整篇論文論證上最大的缺口 |

論文誠實承認的限制還有：

- wiki 沒有自動清理機制，隨著迭代數增加會持續膨脹，論文明講這是留給未來研究的問題。
- 驗證門檻是嚴格的「必須超越最佳分數」，排除了中性但可能有長期價值的提案。
- 目前只驗證到單次 rollout 規模的任務，沒測過真正長時程（數百步、數小時）的場景。

### 四個可以直接帶走的判斷

脫離這篇論文本身，有幾個判斷框架是通用的，值得留在腦子裡：

- **三層分離的設計模式**（不可變的原始紀錄、持續累積且不回滾的結構化知識、可回退的可執行產出）可以直接遷移到其他 agent 演化系統上。
- **訓練時的 actor（這裡是 Inference Agent）不該偷看 optimizer（這裡是 Skill Proposer）用的知識來源**，否則訓練訊號會失真。
- **廣度用全批次摘要拿、深度用有限抽樣或動態檢索做**，是處理「既要全局視野又要個案深度、但 context window 有限」這類問題的通用拆法。
- **做消融實驗時，對照組要精準對應到你想否定的那個具體形式，不能只對照「完全沒有」**。這篇論文最想證明的核心論點，恰好就是全文中唯一沒有被消融實驗直接驗證的一塊，值得引以為戒。

{{< admonition success "三句話帶走" >}}
1. skill 會被整組退版，wiki 不會：WikiSkill 在原始紀錄和 skill 之間多放了一層不會被退版的知識。
2. 證據分級讀：48.7% → 63.7%（Gemini-3.5-Flash 的消融實驗）最紮實，「結構化勝過扁平清單」沒被證明。
3. 自己做的時候，對照組要對準你想否定的那個形式。
{{< /admonition >}}

WikiSkill 在「原始執行紀錄」跟「skill 文件」之間插入一層結構化、永不回滾的知識庫，讓 Skill Proposer 能站在跨迭代累積的證據上做判斷，這是整篇論文最紮實的貢獻，也是本文的核心線索。如果你在做 agent skill 或 memory 系統，三層分離加上永不重置的知識庫這個設計模式，值得直接拿去參考。
