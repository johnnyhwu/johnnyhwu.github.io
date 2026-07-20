---
# weight: 1
title: "[論文介紹] Sparse Upcycling: Training Mixture-of-Experts from Dense Checkpoints"
date: 2024-04-10
lastmod: 2025-09-15
draft: false
description: "探索 Google 發表的 Sparse Upcycling 技術，了解如何將已訓練好的 Dense AI 模型升級為高效的 Mixture-of-Experts (MoE) 模型。本文教你如何用更低的訓練成本，進一步提升模型表現，並避免從零開始訓練的耗時過程。"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Fine-Tuning", "Mixture of Experts"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

[Mixture-of-Experts (MoE)](https://huggingface.co/blog/moe)！相信同樣對 AI 技術深感興趣的你一定對這個詞不陌生~MoE 讓 Deep Neural Network 在許多領域的表現又有了新的突破。

舉例來說，前陣子的 [Mixtral 8x7B](https://mistral.ai/news/mixtral-of-experts/) 透過 MoE 技術讓他的表現逼近或是超越 LLaMA 2 70B，一舉讓 MoE 的技術變的更有名！（題外話：明明 Mixtral 是在 2023 年 12 月被開發出來，距今（2024/4）也還不超過半年，但是感覺已經好久以前的事情了...，AI 領域的進展速度真的快得讓人害怕）

今天並不是要介紹 MoE 的概念，有關 MoE 的概念網路上已經有許多很棒的文章或是教學可以參考，而是要分享一篇筆者最近讀到的有趣的 MoE 相關論文：[Sparse Upcycling: Training Mixture-of-Experts from Dense Checkpoints](https://arxiv.org/abs/2212.05055)。

這是一篇 Google Research 所發行的論文被 ICLR 2023 給接受，都有 Google 和 ICLR 幫我們背書了，想必會是一篇有趣的論文！

今天咱們就花不到 10 分鐘的時間，快速理解這篇論文想要解決什麼問題，以及他所帶來的貢獻是什麼！（小提醒：建議先對 MoE 有個基本的認識，更能幫助你了解這篇文章或是論文的概念哦！）

## 先備知識

在開始介紹 Sparse Upcycling 之前，我們還是先簡單說明一些基本概念，確保我們站在相同的起跑線上！

我們現今所說的 MoE 其實大部分都是 Sparse MoE。「Sparse」的意思是「稀疏的」，用來象徵這個 MoE Model 在運算的過程中並**不會**動用到 Model 中的「所有」參數去和輸入進行運算。

以更高的角度來看，一個 Model 中會有很多 Module（例如：FFN、Self-Attention Layer），對於一個輸入來說，它並不會通過 Sparse MoE Model 中的所有 Module。相較於 Sparse MoE，以前的 Model 大多是 Dense Model。

Dense Model 會把所有的參數都和輸入去做運算。換句話說，一個輸入會通過 Dense Model 中的所有 Module。因此，Dense Model 愈大，運算量也會愈大；Sparse MoE Model 因為讓輸入只和 Model 中部分的參數運算，即使 Model 中的參數變得更多，也不代表運算量會等比例的放大，讓「Model Size」與「Computation Cost (FLOPS)」的連結切開。

通常要把一個（由 Transformer Block 組成的）Dense Model 轉為 MoE Model，就是把 Transformer Block 中的 FFN 換成 MoE Layer！一個 MoE Layer 中會有很多 Expert 以及一個 Router，每一個 Expert 其實也都是一樣的 FFN。

在 MoE Model 中，每一層 MoE Layer 中的 Router 的品質可以說是相當重要！你可以想像，如果這個 Router 品質很差，永遠都把 Input Token 交給某些特定的 Expert 來處理，而沒有根據 Input Token 的特性分給適合的 Expert，那不僅失去了 Mixture of Expert 的精髓，Model 的表現勢必也會不好。

這邊也帶到 Router 的一個重要議題：Expert Load Balance — Router 要如何避免讓某些 Expert 的負擔太重。Router 的 Routing 演算法有很多種，最常見的就是 Top-K Routing 與 Expert Choice Routing。

本篇論文著重在 Expert Choice Routing：假設在一個 MoE Layer 中有 E 個 Expert 與 n 個 Tokens。那 Router 會輸出一個 Routing Matrix (n x E)，每一個 Row 表示這一個 Token 會被每一個 Expert 處理的機率。

換句話說，Routing Matrix 中的每一個 Column 就表示這個 Expert 看每一個 Token 的機率。通常會設定每一個 Expert 看機率最大的 T 個 Token，而 T 其實就是 C x (n / E)，透過 C 來控制每一個 Expert 可以看到的 Token 數量。在 Expert Choice Routing 方式中，有些 Token 會被多個 Expert 看到，有些 Token 則都沒有 Expert 看到。

## Sparse Upcycling 想要解決的問題是什麼

我們來設想一個情境：我們現在手上有一個巨大的模型（Large Dense Model），我們希望更進一步提升它的表現。

最直覺的做法是，繼續訓練它，讓它的 Loss 繼續下降。但是你可以想像，因為模型已經漸趨飽和，即使花了很多時間訓練，Loss 也可能只下降一點點。

好吧，那我們就在模型中加入更多 Module，增加模型的參數量！這麼做確實可以再讓 Loss 隨著訓練進一步下降，但是可想而知，因為模型變得更大，訓練的時間又會變得更久。

換個角度想，如果我們在擴大模型的過程，可以讓模型變成一個 Sparse MoE 架構，是不是就可以解決上述問題？因為在 Sparse MoE 架構下，模型的參數量雖然很大，卻不會直接讓運算量等比例放大。換句話說，大大增加 Model Capacity 的同時，又不會讓 Computation Cost 增加太多！Sparse MoE 正是我們所想要的！

我們再設想另外一個情境：我們現在想要訓練一個 Sparse MoE Model，如果我們 From Scratch 的開始訓練，那麼可想而知，會需要很多的訓練資料與訓練時間。打開 Hugging Face，看到上百、上千的 LLM 放在那邊，如果我們可以基於那些已經 Pre-trained 過的 LLM (Dense Model) 繼續訓練我們的 Sparse MoE Model，是不是有可能降低訓練所需的訓練資料與時間？

說到這裡，相信你已經可以大致上明白，其實 Sparse Upcycling 就是希望可以訓練一個 Sparse MoE Model，但是這個 MoE Model 不是 From Scratch 的訓練，而是基於一個已經訓練好的 Dense Model。

## Sparse Upcycling 方法介紹

{{< image src="solution.png" alt="Sparse Upcycling 示意圖：將原本 dense block 的 Layer Norm、Attention 與 MLP 權重複製到 upcycled MoE block，並把 MLP 複製成 E 份專家，再新增一個從頭訓練的 router 對各專家輸出做加權加總" caption="Sparse Upcycling 的 Solution Overview" >}}

上圖清楚呈現 Sparse Upcycling 的做法：Upcycled MoE Block 主要是將 Original Dense Block 中的 MLP Layer 換成 MoE Layer，其餘的 Layer 的 Weight 都是來自原本的 Block。

此外，MoE Layer 中的 Expert 的 Weight 也是來自原來的 Block 中的 MLP。在訓練 Upcycled Model 時，會使用和訓練 Original Model 完全一樣的 Training Setting。

再講得簡單一點：Sparse Upcycling 就是把原來的 Dense Model 中的部分 MLP Layer 換成 MoE Layer，然後繼續訓練。 雖然 AI 很多概念上都很簡單，但是在實作上其實會有很多細節需要處理，論文中就詳述了以下許要處理的細節：

*   **Router 類型**: 針對 Upcycled MoE Model，作者針對 Vision Model (Encoder)、Language Model 的 Encoder 使用 Expert Choice Routing，針對 Language Model 的 Decoder 使用 Top-K Routing
*   **MoE Layers 的數量**: 把愈多的 MLP Layer 換成 MoE Layer 可以加大 Model 的 Capacity，但是也會增加模型的訓練成本，而且也會讓模型一開始的表現下降得更多。所以是一個 Tradeoff！作者依照過去的方法，將 Model 中一半的 MLP Layer 換成 MoE Layer
*   **Experts 的數量**: 在一個 MoE Layer 中加入更多 Expert 也可以加大 Model 的 Capacity，也會讓模型在訓練初期的表現相較於原來的 Dense Model 下降較多。注意：增加一個 MoE Layer 中的 Expert 數量不太會增加 FLOPS，因為 Expert 愈多，一個 Expert 可以處理的 Token 數量就愈少，因為在 Expert Choice Routing 中，每一個 Expert 可以看到的 Token 數量是 T = C x (n/E)。作者發現一個 MoE Layer 中有 32 個 Expert 的效果最好！
*   **Expert Capacity**: Expert Capacity 代表一個 Expert 可以處理多少 Token：T = C x (n/E)。Expert Capacity 愈大，模型的表現就會愈好，但是也會讓 FLOPS 變得更高。作者發現 C = 2 時，模型的表現已經很好，又不會讓 FLOPS 增加太多。

## Sparse Upcycling 的實驗結果

在實驗中，作者都是拿一個 Dense Model 進行 Upcycle（換成 Sparse MoE 架構）後，然後繼續訓練！

{{< image src="exp-1.png" alt="兩張散點圖，橫軸為額外預訓練時間 (TPU-core-days)，比較 Upcycling (橘色) 與 Dense (藍色) 在 JFT 驗證 precision@1 與 C4 驗證 token accuracy 上的表現，Upcycling 在相同運算下普遍達到更高精度" caption="Sparse Upcycling 實驗結果：Upcycling vs Dense Continuation" >}}

上圖實驗結果呈現的是，在 Vision Model（左圖）與 Language Model（右圖）中，縱軸表示相對應任務的準確度，橫軸表示訓練時間，「Dense」表示基於原來的 Dense Model 繼續訓練。

我們可以發現在少量的訓練預算下，不管是 Vision 還是 Language Model，不管在什麼 Size 之下，Dense 和 Upcycling 的表現都差不多，隨著訓練預算的提高，兩者的差距就會慢慢拉開。說明在使用相同的訓練成本下，繼續訓練 Dense Model 的效率並不好。

{{< image src="exp-2.png" alt="兩張散點圖比較 Upcycling (橘色) 與從頭訓練的 MoE (綠色) 在 JFT 驗證 precision@1 與 C4 驗證 token accuracy 上的表現，Upcycling 在較短的額外預訓練時間下即領先，隨運算增加兩者逐漸接近" caption="Sparse Upcycling 實驗結果：Upcycling vs MoE from Scratch" >}}

與前一個實驗類似，只不過這邊呈現的是 Upcycling 和 MoE (Trained from Scratch) 的表現。可以很合理的發現，Upcycling 因為是基於一個 Dense Model 進行 Upcycle 後再繼續訓練，要達到相同的表現時，Trained from Scratch 到 MoE 一定需要更多的訓練。

透過這兩個實驗結果，其實就呼應了我們在上文「Sparse Upcycling 想要解決的問題是什麼」中所提到的兩個假設情境，透過 Sparse Upcycling 都可以 Performance 與 Training Cost 上更有效率！

## 結語

本篇文章簡單介紹了一篇由 Google Reserach 發表、被 ICLR 2023 所接受的 MoE 相關論文 — [Sparse Upcycling](https://arxiv.org/abs/2212.05055)。

本篇論文告訴我們：其實我們可以善用既有的 Dense Model Checkpoint 來訓練一個 Sparse MoE Model，一方面可以進一步精進 Dense Model 的表現又可以避免 From Scratch 的訓練 Sparse MoE。論文中還有更多細節與描述（尤其是實驗部分），有興趣的讀者再自行閱讀囉！希望本篇文章對你有幫助！

如果你好奇這個想法如何延伸到合併多個獨立訓練的 Dense Expert（而不是 Upcycle 單一模型），可以參考 [Branch-Train-MiX](../branch-train-mix/)，它將 Sparse Upcycling 視為自己更通用框架下的一個特例。
