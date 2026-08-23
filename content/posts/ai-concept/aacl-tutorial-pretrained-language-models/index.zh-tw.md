---
# weight: 1
title: "從 BERTology 到 PEFT：AACL 2022 Tutorial 筆記"
date: 2023-09-01
lastmod: 2023-09-01
draft: false
description: "整理 2022 AACL Tutorial 的內容：BERT 每層學到什麼、為什麼 Sentence Representation 學不好，以及 Adapter、LoRA、Prefix Tuning 等 PEFT 方法如何運作。"
featuredImage: "featured-image.png"

tags: ["Pre-Training", "Large Language Model"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

{{< image src="tutorial-title-slide.png" alt="2022 AACL Tutorial: Recent Advances in Pre-trained Language Models 的標題投影片，上頭列出 Tutorial 名稱與講者。" caption="2022 AACL Tutorial: Recent Advances in Pre-trained Language Models 的標題投影片 [source: 此 Tutorial 投影片的第一頁]" >}}

## 前言

這篇文章整理的是 [AACL-IJCNLP 2022 Tutorial: Recent Advances in Pre-trained Language Models](https://d223302.github.io/AACL2022-Pretrain-Language-Model-Tutorial/) 的內容。目標是給對 NLP 有基本概念、但還沒有系統性摸過 Pre-trained Language Model (PLM) 的人一個大方向的地圖，所以我只挑我覺得最值得記下來的觀念，不會逐頁翻譯整份投影片。想看完整版的話，Tutorial 本身有[影片](https://www.youtube.com/watch?v=thr4-hgLhi8)和[投影片](https://d223302.github.io/AACL2022-Pretrain-Language-Model-Tutorial/lecture_material/AACL_2022_tutorial_PLMs.pdf)。

整篇的主軸其實可以拆成三塊：先搞懂 PLM 到底學到了什麼（#1 ~ #4），再看它學不好的地方以及怎麼補（#5 ~ #8），最後談當模型大到 Finetune 不動時該怎麼辦（#9 ~ #13）。

- #1: Pre-trained Language Model 學的是 Contextualized Word Representation
- #2: BERTology：理解 BERT 每一個 Layer 究竟學到 Language 的什麼知識
- #3: BERT Embryology：理解 BERT 在訓練時期的什麼階段獲得什麼知識
- #4: Pre-trained Language Model 具有 Cross-Discipline 的能力
- #5: BERT 在 Sentence-Level 的 Representation 能力偏廢
- #6: 學習 Sentence-Level 的 Representation 的優點
- #7: BERT-flow 與 BERT-whitening 幫助 BERT 輸出好的 Sentence Representation
- #8: 透過 Contrastive Learning 幫助 BERT 輸出好的 Sentence Representation
- #9: Parameter-Efficient Fine-tuning 的概念
- #10: PEFT: Adapter
- #11: PEFT: LoRA (Low-Rank Adaptation of Large Language Models)
- #12: PEFT: Prefix Tuning
- #13: PEFT: Soft Prompting

## #1: Pre-trained Language Model 學的是 Contextualized Word Representation

{{< image src="contextualized-word-representation.png" alt="示意圖：Pre-trained Language Model 吃進一段句子後，為每個 Word 輸出一個帶有上下文資訊的向量。" caption="Pre-trained Language Model 學得到的是 Contextualized Word Representation" >}}

[Word2vec](https://arxiv.org/abs/1301.3781) 與 [GloVe](https://aclanthology.org/D14-1162.pdf) 學的是 Word Representation：一個 Word 對應一個固定的向量，查表就有。Pre-trained Language Model 不一樣，它學到的是 **Contextualized Word Representation**，同一個 Word 會因為所在的上下文不同而得到不同的 Representation。

{{< image src="word-lie-context-example.png" alt="示意圖：同一個單字 Lie 出現在兩個不同句子裡，模型分別輸出兩個不同的 Representation 向量。" caption="相同的 Word 在不同的 Context 下會有不同的意義，而產生不同的 Representation" >}}

上圖用「Lie」當例子。這個字可以是「說謊」，也可以是「躺著」，語意完全不同。在 Word2vec 的世界裡它只有一個向量，模型得自己想辦法把兩種意思塞進同一個點；在 PLM 裡它會依照上下文生出兩個不同的 Representation，下游任務自然好做很多。

## #2: BERTology：理解 BERT 每一個 Layer 究竟學到 Language 的什麼知識

{{< image src="bert-layerwise-knowledge.png" alt="示意圖：BERT 各層由下而上標註學到的語言知識，底層為表層資訊、中間層為語法、頂層為語意。" caption="BERT 的前面 Layer 學到 Surface 的意義，中間 Layer 學到 Syntactic 的知識，最後幾個 Layer 則是了解整段句子的 Semantic" >}}

知道 PLM 學的是 Contextualized Representation 之後，下一個很自然的問題是：這些知識到底藏在模型的哪裡？這一系列的研究被稱為 BERTology。

作法是用 Probing 技術去分析 BERT 每一層 Layer 輸出的 Representation 裡包含什麼資訊。研究發現，前面幾層主要學到語言中比較表層的知識，中間層開始理解「語法」，最後幾層則負責語意。[BERT Rediscovers the Classical NLP Pipeline (ACL'19)](https://arxiv.org/abs/1905.05950) 這篇論文講得更直白：BERT 從第一層到最後一層做的事情，看起來就像一條傳統的 NLP Pipeline 在處理句子。

不過這個結論後來被修正過。後續研究指出，沒辦法這麼乾淨地劃分每一層各自負責什麼，它們的分工會隨著輸入的 Input 而改變（如下圖右方所示）。

{{< image src="layerwise-knowledge-input-dependent.png" alt="示意圖：同一個模型在不同 Input 下，各層負責的語言知識分布出現變化的比較圖。" caption="Pre-trained Language Model 中每一層學到的資訊是會受到目前的 Input 影響的" >}}

## #3: BERT Embryology：理解 BERT 在訓練時期的什麼階段獲得什麼知識

{{< image src="bert-embryology-training-timeline.png" alt="示意圖：以訓練步數為橫軸，呈現 BERT 在 Pre-train 過程中不同階段習得不同語言能力的概念圖。" caption="BERT Embryology：理解 BERT 在訓練時期學到什麼資訊" >}}

\#2 問的是「知識藏在模型的哪一層」，這裡問的則是另一個維度的問題：「知識是在訓練的哪一個時間點長出來的」。這個題目叫做 BERT Embryology（BERT 胚胎學），名字取得挺傳神的，就是把 Pre-train 的過程當成胚胎發育來觀察，看模型是先學會語法還是先學會語意。

## #4: Pre-trained Language Model 具有 Cross-Discipline 的能力

{{< image src="cross-discipline-finetune-pipeline.png" alt="示意圖：模型先以人類語言做 Pre-train，再 Fine-tune 到 DNA 序列、蛋白質結構等非語言任務的流程圖。" caption="Pre-trained Language Model 具有 Cross-Discipline 的能力" >}}

這裡有個很有意思的實驗設定：Pre-train 階段餵大量的 Human Language，Fine-tune 階段卻換成一個完全不相干領域的任務（例如 DNA 序列的分類、蛋白質結構的分類）。直覺上會擔心模型在 Pre-train 階段學了一堆用不到的語言知識，反而在下游任務上拖後腿。

{{< image src="cross-discipline-bert-vs-random-results.png" alt="實驗結果圖表：BERT 與隨機初始化 (rand) 兩種模型在跨領域下游任務上的分數對照。" caption="有經過 Pre-trained 的 Model (BERT) 表現得仍然比隨機初始化的 Model (rand) 還要好" >}}

結果剛好相反。有經過 Pre-train 再 Fine-tune 的模型 (BERT)，表現仍然勝過隨機初始化後直接 Fine-tune 的模型 (rand)。合理的推測是，Language Model 在 Pre-train 階段學到的不只是那份資料集本身的知識，還包含某些泛化程度更高、跟「怎麼從序列中做分類」有關的能力，換個領域一樣派得上用場。

## #5: BERT 在 Sentence-Level 的 Representation 能力偏廢

前面 #1 ~ #4 講的都是 BERT 的強項。但 BERT 也有明顯的弱點：它在 Word-Level 表現很好，到了 Sentence-Level 就沒那麼漂亮了。

{{< image src="bert-sentence-representation-results.png" alt="實驗結果圖表：BERT 各種取 Sentence Representation 的方式與 GloVe 平均向量在句子相似度任務上的分數比較。" caption="BERT 在 Sentence-Level Representation 上學的不好" >}}

從上圖可以看到，把 BERT 輸出的所有 Token Representation 平均起來當作 Sentence Representation，效果並不好。更尷尬的是，直接把 GloVe 的 Word Representation 平均起來，分數反而還贏過 BERT。

## #6: 學習 Sentence-Level 的 Representation 的優點

既然做不好，那乾脆放棄不學可以嗎？當然不行，好的 Sentence Representation 用途很廣：

- **有一個 Sentence-Level Task 的 Backbone Model**
- **更精準地衡量兩個 Sentence 之間的相似度**
- **提升對 Sentence 做 Clustering 或是 Semantic Search 的準確度**

最直接的例子就是 Semantic Search：使用者打一句查詢，系統要從幾十萬句文件裡撈出語意最接近的那幾句。這件事的品質幾乎完全取決於句向量做得好不好。

## #7: BERT-flow 與 BERT-whitening 幫助 BERT 輸出好的 Sentence Representation

[BERT-flow](https://arxiv.org/pdf/2011.05864.pdf) 這篇論文給了一個解釋：BERT 學不好 Sentence Representation，是因為它在訓練過程中會把 Sentence 投射到一個 Non-Smooth Anisotropic 的空間。白話一點來說，即使 Embedding Space 的維度夠大，BERT 還是傾向把所有句子擠在空間中的某一小塊區域，整個空間的表達能力等於被浪費掉了。句子都擠在一起，算出來的 Cosine Similarity 自然分不出遠近。

{{< image src="bert-anisotropy-embedding-space.png" alt="示意圖：BERT 的句向量在 Embedding Space 中呈現錐狀、集中於狹窄區域的 Anisotropy 現象。" caption="Anisotropy problem in BERT's representation space" >}}

既然問題出在分布，那就從分布下手。[BERT-flow](https://arxiv.org/pdf/2011.05864.pdf) 試圖讓 Sentence Embedding 從 Non-Smooth Anisotropic 的分布轉成 Smooth Isotropic 的高斯分布；[BERT-whitening](https://arxiv.org/pdf/2103.15316.pdf) 則更簡單，直接在後處理階段套用 Whitening 技巧，同樣能讓分布更 Isotropic。兩者都確實拉高了 BERT 的 Sentence Representation 品質。

{{< image src="bert-flow-whitening-results.png" alt="實驗結果圖表：原始 BERT、BERT-flow 與 BERT-whitening 在句子相似度基準上的分數對照。" caption="BERT-flow 和 BERT-whitening 提升 BERT 在 Sentence-Level Representation 的表現" >}}

## #8: 透過 Contrastive Learning 幫助 BERT 輸出好的 Sentence Representation

Self-Supervised Learning (SSL) 這幾年掀起一波熱潮，核心概念是設計一些 Pretext Task，好善用大量沒有標註的 Unlabeled Data 來訓練模型。BERT 本身就是這樣訓練出來的，它的兩個 Pretext Task 是 Masked Language Modeling 與 Next Sentence Prediction。

SSL 的方法大致可以分成 Self-Prediction 與 Contrastive Learning 兩類，BERT 用的那兩個 Pretext Task 屬於前者。而 Contrastive Learning 這幾年在 Computer Vision 上成績相當亮眼，在 ImageNet 的圖像分類問題上甚至已經能勝過用 Supervised Learning 訓練出來的模型。

如果你對 SSL 的概念還不熟，除了 [Hung-Yi Lee 老師的自督導式學習 (Self-supervised Learning) 課程](https://www.youtube.com/watch?v=e422eloJ0W4)，也可以參考這個 [NeurIPS 2021 的 Tutorial](https://www.youtube.com/watch?v=7l6fttRJzeU)（講者是 Lilian Weng）。想快速補齊 Contrastive Learning 在 CV 領域的進展，這支[影片](https://www.youtube.com/watch?v=1pvxufGRuW4)一口氣介紹了 14 篇有名的論文，個人覺得非常有用。

回到正題。這個章節裡講者介紹了一大票用 Contrastive Learning 幫 BERT 學好 Sentence Representation 的論文，大致可以分成七個類別：

- Designed Positives
- Generating Positives
- Bootstrapping Methods
- Dropout Augmentations
- Equivariant Contrastive Learning
- Prompting
- Ranking-based Methods

這七類的差別，講穿了幾乎都在回答同一個問題：**Positive Sample 要從哪裡來**。以下一類一類看。

### Designed Positives

第一類是 **Designed Positives**，透過一些人為設計的機制，從既有資料中挑出 Contrastive Learning 需要的 Positive Samples。

{{< image src="declutr-positive-pair-span.png" alt="示意圖：一份文件中兩個重疊或相鄰的文字 Span 被標示為一組 Positive Pair。" caption="DeCLUTR 透過一份 Document 中 Overlapping 或是 Adjacent 的 Span 來定義 Positive Sample" >}}

[DeCLUTR](https://arxiv.org/abs/2006.03659) 的想法很直覺：同一份 Document 裡，兩個 Span 如果 Overlapping 或是 Adjacent，語意八成很接近，那就把它們當成 Positive Sample。

{{< image src="declutr-vs-bertflow-whitening-results.png" alt="實驗結果圖表：DeCLUTR 與 BERT-flow、BERT-whitening 的分數比較。" caption="DeCLUTR 的表現勝過 BERT-flow 和 BERT-whitening" >}}

從上圖可以看到，Contrastive Learning Based 的方法，表現勝過前一節的 BERT-flow 和 BERT-whitening。

{{< image src="consert-embedding-augmentation.png" alt="示意圖：在 Token 的 Embedding Space 上施加多種 Augmentation 手法以產生 Positive Pair 的流程圖。" caption="ConSERT 在 Token 的 Embedding Space 上做了各種 Augmentation 生成 Contrastive Learning 所需的 Positive Samples" >}}

[ConSERT](https://arxiv.org/abs/2105.11741) 換了個地方動手腳：不在原始文字上做 Augmentation，而是直接在 Token 的 Embedding Space 上做各種 Augmentation 來生成 Positive Samples。

{{< image src="consert-vs-declutr-results.png" alt="實驗結果圖表：ConSERT 與 DeCLUTR 的分數比較。" caption="ConSERT 的表現更勝 DeCLUTR" >}}

從實驗數據可以看到，ConSERT 的表現又更勝 DeCLUTR。

### Generating Positives

前面兩種都是從既有的資料裡「挑」或「改」出 Positive Sample。**Generating Positives** 這一類更乾脆，直接從無到有把 Positive Sample 生出來。

{{< image src="dino-gpt2-positive-generation.png" alt="示意圖：以 GPT-2 為生成器，從一個句子直接生成語意相近句子作為 Positive Sample 的流程圖。" caption="DINO 借助 GPT-2 的力量直接生成 Positive Sample" >}}

[DINO](https://arxiv.org/abs/2104.07540) 就是這個路線的代表，直接借助 GPT-2 的生成能力來產出 Positive Sample。

### Bootstrapping Methods

在 Contrastive Learning 裡，Negative Sample 的數量往往是關鍵，數量太少模型就學不到好的 Representation。這也是實務上很麻煩的一點，因為大量 Negative Sample 通常意味著大 Batch Size 和吃緊的 GPU Memory。不過自從 [Bootstrap Your Own Latent: A New Approach to Self-Supervised Learning (BYOL)](https://papers.nips.cc/paper/2020/file/f3ada80d5c4ee70142b17b8192b2958e-Paper.pdf) 被提出後，我們就有機會在完全不需要 Negative Sample 的情況下做 Contrastive Learning。

{{< image src="byol-bootstrapping-results.png" alt="實驗結果圖表：以 BYOL 方式訓練的句向量方法與含 Negative Sample 的方法之分數比較。" caption="透過 BYOL 幫助 BERT 學習 Sentence Representation (效果不如有包含 Negative Sample 的 Contrastive Learning 方法)" >}}

[Bootstrapped unsupervised sentence representation learning](https://aclanthology.org/2021.acl-long.402/) 這篇正是把 BYOL 的想法搬到 BERT 的 Sentence Representation Learning 上。可惜就上圖的實驗結果來說，還是略遜於有 Negative Sample 的方法（[DeCLUTR](https://arxiv.org/abs/2006.03659)、[ConSERT](https://arxiv.org/abs/2105.11741)、[DINO](https://arxiv.org/abs/2104.07540)）。

### Dropout Augmentations

第四類是 **Dropout Augmentations**，代表作是大名鼎鼎的 [SimCSE](https://arxiv.org/abs/2104.08821)。

{{< image src="simcse-dropout-positive-pair.png" alt="示意圖：同一個句子兩次通過同一個模型，因 Dropout 遮蔽的神經元不同而得到兩個 Embedding。" caption="SimCSE 使用 Dropout 來取代直接對 Input 進行 Augmentation" >}}

[SimCSE](https://arxiv.org/abs/2104.08821) 的作法出乎意料地簡單：不對 Input 做任何 Augmentation，而是對 Transformer Layer 做 Dropout。同一個 Sentence 輸入同一個 Model 兩次，兩次使用相同的 Dropout Probability 但被丟掉的神經元不同，於是得到兩個不同的 Embedding。既然都來自同一個 Sentence，這兩個 Embedding 就是天然的 Positive Sample。

{{< image src="simcse-vs-augmentation-results.png" alt="實驗結果圖表：SimCSE 與 DeCLUTR、ConSERT、DINO 等 Augmentation 方法的分數比較。" caption="SimCSE 的做法勝過其他以 Data Augmentation 為基礎來生成 Positive Sample 的方法" >}}

實驗結果顯示，這種「什麼都不做，只靠 Dropout」的方法，表現比 [DeCLUTR](https://arxiv.org/abs/2006.03659)、[ConSERT](https://arxiv.org/abs/2105.11741)、[DINO](https://arxiv.org/abs/2104.07540) 這些精心設計 Augmentation 的方法都好。

### Equivariant Contrastive Learning

SimCSE 的結果其實暴露了一件事：**要對 NLP 做 Data Augmentation 並不容易**。文字是離散的，改一個字語意可能就整個跑掉，所以再怎麼設計 Augmentation，成績也不如單純對 Model 做 Dropout。

回頭想想，之所以要用 Data Augmentation 產生 Positive Sample，是希望模型學到的 Representation 對這些 Augmentation 是 Invariant 的。但從 DeCLUTR、ConSERT、DINO 到 SimCSE 的比較看下來，這個出發點在 NLP 上反而拉低了模型表現。

{{< image src="equivariant-contrastive-learning-tasks.png" alt="示意圖：左右並列的兩種訓練目標，一邊要求 Representation 對 Augmentation 不變，另一邊要求能反推出施加了哪種 Augmentation。" caption="Equivariant Contrastive Learning 中同時包含兩種 Task" >}}

於是 **Equivariant Contrastive Learning** 提出：有些方法希望透過 Invariance Task 讓模型學到好的 Representation（如上圖左），有些則希望透過 Equivariance Task（如上圖右）。Invariance 是「不管怎麼改，Representation 都要一樣」；Equivariance 反過來，是「Representation 要能反映出你做了什麼改動」。

{{< image src="diffcse-architecture.png" alt="示意圖：DiffCSE 的架構圖，左半邊為 Invariance Task 的 Sentence Encoder，右半邊為 Equivariance Task 的判別分支。" caption="DiffCSE 基於 Equivariant Contrastive Learning 的想法，透過兩種 Task 來訓練 Sentence Encoder" >}}

[DiffCSE](https://arxiv.org/abs/2204.10298) 就是基於 [Equivariant Contrastive Learning](https://arxiv.org/abs/2111.00899) 的想法，同時用兩種 Task 來訓練 Sentence Encoder：左半邊做 Invariance Task，右半邊做 Equivariance Task。實際 Inference 時只會用到左半邊的 Sentence Encoder，右半邊純粹是訓練時期的輔助。

{{< image src="diffcse-vs-simcse-results.png" alt="實驗結果圖表：DiffCSE 與 SimCSE 在句子相似度基準上的分數比較。" caption="DiffCSE 比 SimCSE 表現得更好" >}}

從實驗結果可以看到，DiffCSE 比 SimCSE 好了約 2% – 3%。

### Prompting

第六類是 **Prompting**，代表論文為 [PromptBERT: Improving BERT Sentence Embeddings with Prompts](https://aclanthology.org/2022.emnlp-main.603/)。

{{< image src="promptbert-template.png" alt="示意圖：把句子填入含有佔位符的 Prompt Template，再取遮罩位置的 Hidden State 作為句向量。" caption="透過設計 Prompt Template 來學習 Sentence 的 Embedding" >}}

PromptBERT 設計了一些 Prompt Template，把要編碼的 Sentence 插到 Template 的 `[X]` 位置，再把整個 Prompt 丟進 BERT，取 `[MASK]` Token 對應的 Hidden State 當作這個 Sentence 的 Embedding。這樣做等於是讓 BERT 用它最熟悉的 Masked Language Modeling 姿勢輸出句向量，而不是硬去平均一堆 Token。

### Ranking-based Methods

最後一類是 **Ranking-based Methods**，代表方法是 [RankEncoder: Ranking-Enhanced Unsupervised Sentence Representation Learning](https://arxiv.org/pdf/2209.04333.pdf)。它的切入點是：一個 Sentence 的語意，可以用它跟其他句子的相對關係來描述。

{{< image src="rankencoder-rank-vector-pipeline.png" alt="示意圖：兩個句子分別與外部語料庫比對相似度後形成 Rank Vector，再以內積得到兩者相似度的流程圖。" caption="RankEncoder 透過鄰居資訊來學習一個 Sentence 的 Embedding" >}}

具體作法是：給定兩個 Sentence，分別計算它們與外部 Corpus 中每個 Sentence 的相似度，各自建立一個 Rank Vector。把這兩個 Rank Vector Normalize 後做內積，就得到這兩個 Sentence 的 Similarity。上圖右下角是訓練目標：RankEncoder 要學會把這兩個 Sentence 轉成好的 Representation，使得兩者的 Cosine Similarity 逼近用「鄰居資訊」算出來的 Similarity。

{{< image src="rankencoder-sota-results.png" alt="實驗結果圖表：RankEncoder 與前述各種句向量方法的分數總表。" caption="透過 RankEncoder 學習出來的 Sentence Representation 達到 SOTA" >}}

從上圖可以看到，[RankEncoder](https://arxiv.org/pdf/2209.04333.pdf) 的表現幾乎比前面介紹的所有方法都來得好。

## #9: Parameter-Efficient Fine-tuning 的概念

{{< image src="standard-finetune-per-task-models.png" alt="示意圖：一個 Pre-trained Model 被完整複製並針對多個下游任務各自訓練成一份獨立模型。" caption="一般的 Finetune 方式中，會對整個 Pre-trained Model 訓練在下游任務" >}}

拿到一個 Pre-trained Model 之後，一般作法是把它 [Finetune 到下游任務](../llm-fine-tuning-rlhf/)。問題是這個「一般作法」的成本相當可觀：假設有 5 個下游任務，就要對「整個」Pre-trained Model 訓練 5 次，最後手上會有 5 份跟原模型幾乎一樣大的權重要存。

隨著 Pre-trained Model 愈做愈大，這條路很快就走不通了。受限於 GPU Memory，一般人幾乎沒辦法對整個模型做 Finetune。我們需要一種在 Finetune 階段不用動到那麼多參數的方法，這一系列作法就叫做 **Parameter-Efficient Fine-tuning (PEFT)**。

{{< image src="peft-extra-module-finetune.png" alt="示意圖：Pre-trained Model 主體維持凍結，只在其中插入小型模組並針對這些模組訓練的架構圖。" caption="Parameter-Efficient Fine-tuning 在 Pre-trained Model 中加入額外的模組，並只針對這個額外的模組進行 Finetune" >}}

PEFT 的作法是在 Pre-trained Model 中插入額外的小模組，Finetune 階段只訓練這些模組。這樣一來，每個下游任務要保存的就不再是一整份大模型，而只是那些額外模組的參數。

那為什麼只動一小撮參數也能work？這要回頭看 Finetune 的本質：**Finetune 是希望改變 Pre-trained Model 的 Representation，使其在下游任務有更好的表現**。

{{< image src="finetune-representation-h-to-hprime.png" alt="示意圖：原始 Representation h 經過 Finetune 後變成 h_prime，兩者之間差一個 delta_h 的概念圖。" caption="Finetune 是希望改變 Pre-trained Model 的 Representation，使其在下游任務有更好的表現" >}}

上圖把這件事講得很清楚：原本 Pre-trained Model 的 Representation 是 h，整個模型 Finetune 完之後 Representation 變成 h_prime。既然目的只是要從 h 走到 h_prime，那何必動整個模型？PEFT 的核心思想就是加一個小模組去產生額外的 delta_h，讓 h + delta_h = h_prime。

PEFT 主要有 4 種實現方法，以下逐一介紹：

- Adapter
- LoRA
- Prefix Tuning
- Soft Prompting

## #10: PEFT: Adapter

{{< image src="adapter-architecture.png" alt="示意圖：Transformer Layer 中在 Self-Attention 與 Feed-Forward 之後各插入一個 Adapter 模組，右側放大顯示 Adapter 內部的兩層 Feed-Forward 與 Skip Connection。" caption="Adapter 示意圖" >}}

Adapter 的概念就是在一個 Transformer Layer 中的 Multi-Head Self-Attention 後方，以及 Feed-Forward Layer 的後方，各額外加上一個小模組，這個模組就叫 Adapter。它的架構如上圖右方所示：兩個 Feed-Forward Layer 中間夾一個 Non-Linear Layer，外加一個 Skip Connection。

對照 #9 的 h 與 delta_h：兩個 Feed-Forward Layer 加上 Non-Linear Layer 負責把原來的 Representation h 轉換成 delta_h，Skip Connection 則負責把 h 與 delta_h 相加，得到 Finetune 後的 h_prime。

## #11: PEFT: LoRA (Low-Rank Adaptation of Large Language Models)

{{< image src="lora-overview-architecture.png" alt="示意圖：Transformer Layer 的 Feed-Forward Layer 旁邊並聯一組額外模組的整體架構圖。" caption="LoRA 示意圖" >}}

LoRA 的作法是在 Transformer Layer 中的 Feed-Forward Layer 旁邊，多掛上一些模組。

{{< image src="lora-feedforward-branch.png" alt="示意圖：Feed-Forward Layer 的兩層結構旁並聯一個同樣由兩層組成的旁支模組。" caption="LoRA 的作法是在 Transformer Layer 的 Feed-Forward Layer 旁額外加上一個分支" >}}

具體來說，Transformer Layer 中的 Feed-Forward Layer 實際上由兩個 Layer 組成，LoRA 就是在這兩個 Layer 旁邊再加一個分支，而這個分支同樣由兩個 Layer 組成。

{{< image src="lora-low-rank-projection.png" alt="示意圖：輸入向量先被降維到一個很小的維度，再被放大回原本維度，輸出與主幹相加。" caption="LoRA 模組會將原來的 Representation 投射到一個特別小的維度上後，再放大得到新的 Representation" >}}

比較特別的是，LoRA 模組會先把原來的 Input 投射到一個特別小的維度，再放大回去得到新的 Representation (delta_h)，最後與原來的 Representation (h) 相加得到 h_prime。這個「先壓扁再放大」正是 Low-Rank 的意思，也是它參數量能壓這麼低的原因。

## #12: PEFT: Prefix Tuning

從字面上看，Prefix 就是加在某個東西「前面」的東西，而 Prefix Tuning 就是只針對這些加在前面的東西做 Finetune。

要理解它怎麼運作，得先複習一下 Self-Attention。

{{< image src="self-attention-mechanism.png" alt="示意圖：Sequence 中每個向量經 Query、Key、Value Projection 後，以 Attention Score 對所有 Value 做加權和的運算流程圖。" caption="Self-Attention 的原理" >}}

上圖呈現的是 Self-Attention 的原理：Sequence 中的每一個 Vector 都會透過一組 Query Projection、Key Projection 與 Value Projection，得到自己的 Query、Key 與 Value。當我們要計算 x1 的輸出時，會拿 x1 的 Query 去跟所有 Vector（包含它自己）的 Key 做運算，得到 Attention Score，代表 x1 跟每個 Vector 有多相關。接著用 Attention Score 對所有 Vector 的 Value 做 Weighted Sum，就是 x1 的輸出。

在 Prefix Tuning 中，我們會在 Self-Attention Layer 的輸入「前面」多加上一些 Vector，這些 Vector 就稱為 Prefix。

{{< image src="prefix-tuning-input-sequence.png" alt="示意圖：Self-Attention 的輸入序列前方插入數個額外向量，這些向量同樣參與 Attention 運算。" caption="Prefix Tuning 就是在 Self-Attention Layer 的 Input Sequence 的前方再多加入一些 Vector" >}}

如上圖所示，多了 Prefix 之後，計算 x1 的輸出時就得把 Prefix 的 Query、Key 和 Value 一起算進去。原來那些 Vector 的 Value 做 Weighted Sum 得到原本的 Representation (h)，Prefix 的 Value 做 Weighted Sum 得到 delta_h，兩者加總後就是 Finetune 過後的 h_prime。同樣是 h + delta_h 的老套路，只是這次 delta_h 來自 Attention 本身。

## #13: PEFT: Soft Prompting

Adapter、LoRA 與 Prefix Tuning 算是 PEFT 中最常見的三種手法，第 4 種、也是最常被忽略的是 Soft Prompting。

{{< image src="soft-prompting-prefix-embedding.png" alt="示意圖：Input Sequence 經 Embedding Layer 得到的 Embedding 前方，接上數個可訓練的 Prefix Embedding 一起送入 Transformer。" caption="Soft Prompting 就是在 Embedding Layer 的輸出額外加上一些 Prefix Embedding" >}}

Soft Prompting 動手的位置更靠前：原來的 Input Sequence 經過 Embedding Layer 後會得到一串 Embedding（上圖藍色部分），我們額外接上一些 Prefix Embedding，再把它們一起送進 Transformer。這些 Prefix Embedding 是可訓練的向量，不需要對應到任何真實的字。

{{< image src="hard-prompting-input-words.png" alt="示意圖：直接在原始輸入文字前面加上實際單字，再送入 Embedding Layer 的對照示意圖。" caption="Hard Prompting 則是直接在 Input Sequence 中加入額外的 Word" >}}

Soft Prompting 的相反是 Hard Prompting，也就是我們一般認知的 Prompt：直接在最一開始的 Input Sequence 中加入額外的 Word。差別在於 Hard Prompting 加的是人看得懂的文字，Soft Prompting 加的是模型自己學出來、人看不懂的向量。

## 結論

這篇整理了 [AACL-IJCNLP 2022 Tutorial: Recent Advances in Pre-trained Language Models](https://d223302.github.io/AACL2022-Pretrain-Language-Model-Tutorial/) 中我認為最值得記下來的**部分**知識點，從 PLM 學到什麼、Sentence Representation 為什麼難、到 PEFT 的四種主流作法。

回頭看，PEFT 那條線在這幾年變得特別重要，LoRA 幾乎已經成為微調大型模型的預設選項。文章中大部分的插圖都節錄自這個 Tutorial，如果想看更完整的內容，建議直接看[影片](https://www.youtube.com/watch?v=thr4-hgLhi8)或是[投影片](https://d223302.github.io/AACL2022-Pretrain-Language-Model-Tutorial/lecture_material/AACL_2022_tutorial_PLMs.pdf)。
