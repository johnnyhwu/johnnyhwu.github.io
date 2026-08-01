---
# weight: 1
title: "機器學習基本觀念：Bias-Variance Tradeoff"
date: 2026-06-16
lastmod: 2026-06-16
draft: false
description: "模型的 Error 由 Bias 與 Variance 組成，而且降低一個往往會推高另一個。本文用身高預測體重的例子，說明 Underfitting、Overfitting 與兩者之間的權衡。"
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

模型訓練完之後，我們會用測試資料集來衡量它的效能，也就是計算模型的 Error。這個 Error 其實由兩個部分組成：Bias 與 Variance。理想上兩個都愈小愈好，但現實是「魚與熊掌不可兼得」，降低 Bias 往往會讓 Variance 變高，反過來壓低 Variance 又會把 Bias 拉上去。

本文會說明什麼是模型的 Bias 與 Variance、兩者為什麼會互相拉扯，以及模型該訓練到什麼程度才算取得平衡。

閱讀之前，建議先對「什麼是機器學習」、「機器學習的模型、訓練與推論」以及「機器學習五步驟」這幾個主題有基本的概念（本系列前幾篇文章都有介紹）。

{{< admonition abstract "重點整理 (TL;DR)" >}}
- **Bias** 是模型的輸出與正確答案之間的誤差。Bias 大代表模型沒學到輸入與輸出的關係，屬於 **Underfitting**。
- **Variance** 是模型針對不同輸入資料時，輸出的變異程度。Variance 大代表模型連訓練資料中的雜訊都背了起來，屬於 **Overfitting**。
- 兩者會隨模型複雜度**往相反方向移動**，所以無法同時最小化。
- 真正要追求的不是把某一項壓到最低，而是讓 **Total Error 落在 U 型曲線的谷底**。
{{< /admonition >}}

## Model 的 Bias

拿到訓練資料集之後，我們就會開始用這些資料訓練模型。所謂訓練，講白了就是不斷調整模型裡的參數，讓資料丟進去之後，模型的輸出愈接近正確答案 (Label) 愈好。換個角度看，模型就是一個 Function，負責把輸入資料對應 (Mapping) 到某個輸出。

用一個很小的訓練資料集來說明。資料集裡只有 5 個樣本，每個樣本都有「身高」與「體重」兩個數值。我們希望把「身高」輸入模型，模型吐出「體重」，也就是用身高預測體重。

每個樣本用 (x, y) 表示，x 是身高，y 是體重：

1. (160, 60)
2. (163, 70)
3. (165, 72)
4. (168, 75)
5. (170, 70)

把這 5 個樣本畫在 2 維平面上，長這樣：

{{< image src="5-simples-dataset.jpg" alt="5 個樣本的身高與體重資料點分佈在 2 維座標平面上的散佈圖。" caption="一個簡單的訓練資料集" >}}

假設我們用這個資料集訓練出一個模型，也就是下圖中的那條紅線：

{{< image src="linear-regression.jpg" alt="同一組資料點上多了一條紅色直線，代表用這 5 個樣本訓練出來的模型。" caption="利用這 5 個樣本訓練出來的模型" >}}

這時候會發現一件事：輸入身高 = 163，模型輸出的體重並不是 70。輸入 165、168、170 也一樣，模型給的答案都跟正確答案有落差。

**模型的輸出與正確答案之間的誤差，就稱為 Bias**，也就是下圖中灰色框框標示出來的距離：

{{< image src="error-in-linear-regression.jpg" alt="資料點與紅色回歸線之間以灰色框框標示出誤差距離的示意圖。" caption="框框呈現的是模型的輸出與正確答案的誤差" >}}

當模型的 Bias 很大，代表它要嘛訓練得不夠徹底，要嘛複雜度太低，總之就是沒有從訓練資料集裡學到該學的東西，根本沒搞懂輸入與輸出之間的關係。這種模型拿到一筆身高資料，可能會給出一個錯得離譜的體重。我們會說這個模型 **Underfitting**。

## Model 的 Variance

看到這裡，你八成會想到一個解法：「那我用一個超級複雜的模型，一路訓練到每一筆樣本都預測得分毫不差不就好了？」照這個思路做下去，你大概會得到這樣的模型：

{{< image src="overfitting-model.jpg" alt="一條高度彎曲的曲線精準穿過全部 5 個資料點的示意圖。" caption="訓練模型精準的預測每一個樣本" >}}

這條曲線看起來完美，訓練資料集裡的每一筆數據它都命中。問題出在沒看過的資料上：輸入身高 = 169，模型的輸出可能落在 72 附近；輸入身高 = 170，模型輸出 70；輸入身高 = 175，模型的輸出卻可能掉到 60。

明明身高只差幾公分，模型的輸出卻上下劇烈跳動。**針對不同的輸入資料，模型輸出的變化（變異性）分佈就稱為 Variance**。

Variance 很大，代表模型把訓練資料集裡的所有東西都硬吞了進去，連「雜訊」也一起學。以上面那條曲線為例，一般來說身高愈高、體重也會愈重，所以第 5 個樣本 (170, 70) 相對於前面的趨勢就可以視為雜訊。模型把這筆雜訊也學起來之後，就會得出一個荒謬的結論：「身高愈高體重愈重，但只要超過 168，體重就會突然暴跌」。

說穿了，這種模型同樣沒有理解輸入與輸出之間的關係，只是把每一筆樣本的對應關係死背下來。一旦餵給它一筆從沒見過的身高，它照樣可能給出錯得離譜的答案。這種模型我們稱為 **Overfitting**。

## Bias-Variance Tradeoff

到這裡兩個極端都出現了：模型太簡單會 Underfitting，太複雜會 Overfitting。這兩者跟 Bias、Variance 的對應關係，可以用下圖來理解：

{{< image src="underfiting-and-overfitting.png" alt="以射靶方式呈現 Bias 與 Variance 高低組合的示意圖，並對應到 Underfitting 與 Overfitting 兩種情況。" caption="Bias-Variance 與 Underfitting-Overfitting 的關係 [source: Towards Data Science]" >}}

模型非常「複雜」（參數量很大）時，有能力把訓練資料集裡的每個樣本都記下來，此時 Variance 很高、Bias 很低，也就是前面說的 Overfitting；模型過於「簡單」（參數量很小）時，根本學不到東西，此時 Bias 很高、Variance 很低，也就是 Underfitting。

回到開頭那句話：模型的 Total Error 同時包含 Bias 與 Variance。既然壓低其中一個就會推高另一個，我們就必須在兩者之間權衡，找出讓 Total Error 最低的那個點，這就是 **Bias-Variance Tradeoff**。

下圖把這件事畫得很清楚：

{{< image src="bias-variance-tradeoff.png" alt="Bias 與 Variance 隨模型複雜度變化的兩條曲線，以及兩者相加後呈 U 型的 Total Error 曲線。" caption="Bias-Variance Tradeoff 的意義 [source: scott.fortmann-roe.com]" >}}

橫軸是模型複雜度，Bias 隨著複雜度上升而下降，Variance 則反過來上升，兩條線相加得到的 Total Error 呈現 U 型。只盯著 Bias 或只盯著 Variance 調整，都不會落在 U 型的谷底。實務上要找的，就是那個讓 Total Error 最小的甜蜜點。

## 結論

模型的 Error 由 Bias 與 Variance 組成：Bias 大代表模型沒學到輸入與輸出的關係，屬於 Underfitting；Variance 大代表模型把訓練資料連雜訊一起背了起來，屬於 Overfitting。兩者會隨模型複雜度往相反方向移動，所以調模型時真正該追的不是把某一項壓到最低，而是讓 Total Error 落在 U 型曲線的谷底。

下次在調整模型架構或訓練輪數時，不妨先判斷目前卡在哪一端：訓練誤差就降不下來，多半是 Bias 的問題；訓練表現好、測試表現差，那就是 Variance 在作祟。

### 參考資料

- [Understanding the Bias-Variance Tradeoff | by Seema Singh | Towards Data Science](https://towardsdatascience.com/understanding-the-bias-variance-tradeoff-165e6942b229)
- [What is the tradeoff between Bias and Variance? (educative.io)](https://www.educative.io/edpresso/what-is-the-tradeoff-between-bias-and-variance)
