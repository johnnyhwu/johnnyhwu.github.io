---
# weight: 1
title: "一篇文搞懂 Dropout：為何它能有效解決神經網路的 Overfitting？"
date: 2022-08-06
lastmod: 2025-11-01
draft: false
description: "訓練神經網路時遇到 Overfitting？本文將帶你深入了解 Dropout 原理，從 Ensemble 和 Co-Adaptation 的角度，解釋為何這個簡單的技巧能有效解決模型過擬合問題"
featuredImage: "featured-image.png"

tags: []
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## 前言

在訓練 Neural Network 時，如果 Network 過於複雜（參數量很多），但是擁有的訓練資料又很少，就容易發生 **Overfitting** 的問題。如果你對於 Overfitting 的觀念不太了解，可以參考這篇關於 [Bias-Variance Tradeoff 觀念](../bias-variance-tradeoff/)的介紹。

在實際訓練時，如果 Model 已經 Overfitting 則會出現 Training Error 不斷下降，Validation Error 降不下去的窘境。解決 Overfitting 的技巧很多，Dropout 算是其中一個基本的技巧。不管你在哪裡學習 Deep Learning 的知識，如果訓練 Neural Network 遇到 Overfitting 的狀況，勢必會告訴你在 Linear/Dense Layers 中插入一層 Dropout Layer！

然而，你真的了解 Dropout Layer 到底對 Neural Network 做了什麼事情嗎？本文將會帶你認識 Dropout 從何而來、Dropout 的原理、Dropout 的實作方式，最後則是 Dropout 為什麼可以解決 Overfitting 的問題。

## Dropout 從何而來

Dropout 的概念來自於 Hinton 於 2012 年所發表的論文「[Improving neural networks by preventing co-adaptation of feature detectors](https://arxiv.org/abs/1207.0580)」。

在論文中的摘要提到： When a large feedforward neural network is trained on a small training set, it typically performs poorly on held-out test data. This “overfitting” is greatly reduced by randomly omitting half of the feature detectors on each training case. This prevents complex co-adaptations in which a feature detector is only helpful in the context of several other specific feature detectors. （雖然每一個英文單字都看得懂，但是合成一整句就看不懂）

他的意思大概是說，當我們有一個很複雜的模型（參數量很大），但是只有少少的訓練資料時，模型很容易因此而 Overfitting。如果能夠在模型「訓練過程」，減少 Neural Network 中 Neuron（Feature extractor） 之間的「共同適應」就能有效緩解 Overfitting 的問題。「共同適應」是什麼概念？我們在接下來的文章中會繼續說明。

在同年，Alex、Hinton 等人發表了「[ImageNet Classification with Deep Convolutional Neural Networks](https://proceedings.neurips.cc/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf)」論文，論文中使用 AlexNet 進行圖像分類的任務，並在訓練過程使用 Dropout 減緩模型的 Overfitting，成功贏得 2012 年的 ImageNet 競賽（還狠狠的屌打第二名）。

自此之後，Deep (Convolution) Neural  Network 一炮而紅，大家開始瘋狂使用 Deep (Convolution) Neural  Network 處理電腦視覺相關任務，Dropout 也因此成為避免模型 Overfitting 的基本技巧。

## Dropout 原理（簡易版）

接著，讓我們從簡易的觀點理解 Dropout 的運作原理！

{{< image src="concept.png" caption="Dropout 會隨機選擇部分 Neuron 使得其 Activation 為 0" >}}

如上圖（a）所示，我們建立了一個 Neural Network。在一般情況下，我們會輸入 x 到 Neural Network，並根據 Neural Network 的輸出 y 計算這一個 Batch 的 Cost。有了 Cost 後，我們就可以利用 Gradient Descent 的概念更新 Neural Network 中的所有參數。

{{< admonition info >}}
如果你還不了解 Neural Network 是如何更新參數的，可以參考：

- [Deep Learning 基本功：Gradient Descent 介紹](../gradient-descent/)
- [Stochastic Gradient Descent 介紹](../stochastic-gradient-descent/)
- [Backpropagation 介紹 —— 看懂如何透過 Backpropagation 計算 Gradient](../backpropagation/)

{{< /admonition >}}

如果我們在訓練過程中使用了 Dropout Layer ，我們的 Neural Network 會由（a）變成（b）。在 [TensorFlow API](https://www.tensorflow.org/api_docs/python/tf/keras/layers/Dropout) 與 [PyTorch API](https://pytorch.org/docs/stable/generated/torch.nn.Dropout.html) 中，當我們在初始化 Dropout Layer 時，都需要傳入一個「機率」，表示每個 Neuron 有多大的機率會「停止運作」。

所謂的「停止運作」指的是不管我們輸入什麼到 Neural Network 中，這些 Neuron 的輸出（Activation）永遠都是 0。當 Neuron 的輸出為 0，不管連接的 Weight 有多大，相乘以後的結果一定都是 0。

此外，在 Backpropagation 的過程中，如果某一個 Weight 其 Input（上一層的 Activation）為 0，將會導致 Gradient 亦為 0，使得這一個 Weight 無法被更新。

因此，在上圖（b）中，我們以（✕）來表示停止運作的 Neuron，並將其連接的線段（Weight）去除，整個 Neural Network 就像是沒有這些 Neuron 的存在。

如果你不了解為什麼 Gradient 為 0，可以參考這篇文章：[Backpropagation 介紹 —— 看懂如何透過 Backpropagation 計算 Gradient](../backpropagation/)

當我們要輸入下一個 Input Batch 到 Neural Network 時，Dropout Layer 會將剛剛停止運作的 Neuron 恢復正常，再重新選擇新的一批 Neuron 來停止運作。就這樣重複進行相同的操作，在每一個 Iteration 中，都有一部份的 Neuron 不會對 Neuron Network 的輸出有所貢獻，連接他們的 Weight 當然也不會被更新。

## Dropout 原理（詳細版）

如果你已經看懂 Dropout 的基本觀念，讓我們再以數學的角度來理解 Dropout 的原理吧！

{{< image src="concept-2.png" caption="Dropout 會使得每一個 Neuron 以固定的機率將其輸出設為 0" >}}

如上圖所示，在一般的 Neural Network 中，前一層的輸出 y 會直接與這一層的 Weight 相乘，並加上 Bias；若加上 Dropout 機制，會使得前一層的每一個輸出 y，都會再乘以一個 r 才會與這一層的 Weight 相乘，並加上 Bias。

這裡的 r 是由 Bernoulli Distribution 以機率 p 生成的一個數字，r 可能為 0 或 1。當 r 為 0 時，表示這一個 Neuron 停止運作，因為其輸出將會被設為 0。

{{< image src="concept-3.png" caption="Dropout Network 公式" >}}

上圖是以數學算式呈現一般的 Neural Network 與加入 Dropout 機制的不同之處，可以發現其實只有多了紅色部分，也就是每一個 Neuron 都會從 Bernoulli Distribution 以機率 p 生成出 0、以機率 (1-p) 生成出 1。

假設 Dropout Layer 前一層為 Dense/Linear Layer，裡頭共有 1000 個 Neuron。如果我們將 Dropout Layer 的機率 p 設為 0.5，則每一個 Neuron 都會有 50% 的機率被停止運作，換句話說，1000 個 Neuron 中約有 500 個 Neuron 會被停止運作（500 個 Neuron 的輸出會被設為 0）。

需要特別注意的是，我們必須確保每一個 Neuron 在「訓練階段」與「測試階段」其**輸出的期望值不變**。

{{< image src="concept-4.png" caption="Dropout 機制下 Neuron 的輸出期望值為 (1-p) * y" >}}

如上圖算式所示，在「訓練階段」受到 Dropout 機制影響下的 Neuron 有 p 的機率輸出會變成 0（停止運作），有 (1-p) 的機率輸出維持不變。因此，該 Neuron 的輸出期望值會是 (1-p) * y。

為了確保該 Neuron 在訓練階段與測試階段中，輸出的期望值皆相同，我們可以選擇**在「訓練階段」時，對該 Neuron 的輸出乘以 1 / (1-p)** 或是**在「測試階段」時，對該 Neuron 的輸出乘以 (1-p)**。

## Dropout 為什麼可以解決 Overfitting

完全理解的 Dropout 的運作原理後，我們再回過頭想想為什麼 Dropout 機制可以有效解決 Overfitting 的問題？

我們可以試著從兩個面向說明：

第一個面向為「**Ensemble**」 的概念。

在 [Ensemble Learning](https://machinelearningmastery.com/tour-of-ensemble-learning-algorithms/) 中，我們會訓練多個模型，並一起考慮多個模型的預測結果，作為最終的預測結果。在 Ensemble Learning 中透過取平均或是多數決的概念，來提升模型整體的表現。

Dropout 機制就像是一種 Ensemble 的概念：在每一個 Iteration 中，我們都會「停止運作」某些 Neuron，就像是從 Neural Network 將這些 Neuron 去除一樣，因此每一個 Iteration 我們都可以得到一個「不同結構」的 Neural Network。

最終，在整個 Neural Network 的訓練過程，表面上看起來是在訓練單一個模型，但是實際上是綜合了各種不同結構的模型。因此，Neural Network 的輸出也不單單只是「一個」Neural Network 的輸出，而是「多個」Neural Network 輸出的綜合結果。

第二個面向為「**Co-Adaptation**」的概念。

Co-Adaption 的中文為「共同適應」，指的就是 Neuron 之間的依賴關係。舉例來說，假設 Neural Network 中「第二層第一個」 Neuron 接受來自「第一層」所有 Neuron 的輸出，但是相對**較為依賴**「第一層第一個」 Neuron 所輸出的值。這樣使得雖然「第二層第一個」 Neuron 表面上接受來自「第一層」所有 Neuron 的特徵，但實際上只在意「第一層第一個」 Neuron 的特徵。

因為我們不希望 Neuron 只對**單一特徵**過度敏感，透過 Dropout 機制，使得「第一層第一個」 Neuron 與「第二層第一個」 Neuron 不一定會同時出現，迫使「第二層第一個」 Neuron 要學習從「第一層」其他 Neuron 的特徵學習。

如果 Neural Network 中每一個 Neuron 都是考慮了前一層所有 Neuron 的特徵，而不依賴於單一特徵，即使輸入的所有特徵中包含了一些瑕疵，也不會受到太大的影響，當然會使得整個模型的 Generalization 能力更棒。

## 結語

在本篇文章中，我們介紹了 Deep Learning 中專門用來對付 Overfitting 的經典技巧「Dropout」的運作原理，了解 Dropout 在訓練與測試階段分別對 Neural Network 做了什麼事情，並透過「Ensemble」與「Co-Adaption」的概念，解釋 Dropout 為什麼可以解決 Overfitting，提升模型的表現。

## 參考

- [Improving neural networks by preventing co-adaptation of feature detectors](https://arxiv.org/abs/1207.0580)
- [ImageNet Classification with Deep Convolutional Neural Networks](https://proceedings.neurips.cc/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf)
- [AlexNet - 維基百科，自由的百科全書 (wikipedia.org)](https://zh.wikipedia.org/zh-tw/AlexNet)
- [深度学习中Dropout原理解析 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/38200980)
- [Co-adaptation - Machine Learning Glossary](https://machinelearning.wtf/terms/co-adaptation/)
