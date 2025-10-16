---
# weight: 1
title: "告別 ONNX 模型黑盒子：使用 onnx-tool 實現完美 Shape Inference 與 Profile，讓 Netron 顯示所有細節"
date: 2023-06-11
lastmod: 2025-10-16
draft: false
description: "探索 'onnx-tool'：一款強大的 ONNX 分析工具，能輕鬆完成 Shape Inference 與模型 Profile。解決 Netron 無法顯示的動態 Shape 問題，深入分析參數量、運算量，讓你全面掌握你的 AI 模型。"
featuredImage: "featured-image.png"

tags: ["ONNX"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->


## 前言

本篇文章想介紹一款好用的 ONNX 工具給讀者，可以更簡單、更有效率的方式來對 ONNX 進行 Profile 與 Shape Inference。ONNX 是什麼？！

這裡引用 [Wiki](https://zh.wikipedia.org/zh-tw/ONNX?useskin=vector) 對 ONNX 的介紹：「**ONNX**（英語：Open Neural Network Exchange）是一種針對機器學習所設計的開放式的文件格式，用於存儲訓練好的模型。它使得不同的人工智慧框架（如 Pytorch、MXNet）可以採用相同格式存儲模型數據並交互」。

沒錯！ONNX 最大的優點就是可以讓我們的 Neural Netowork 在不同的 Framework 之間轉換。網路上許多 TensorFlow 與 PyTorch 模型互相轉換的工具，大多也是基於 ONNX 實作的：先將模型由原始格式轉為 ONNX 格式，再轉為 TensorFlow。

## ONNX 視覺化工具：Netron

說到 ONNX 就不可以不提到 [Netron](https://github.com/lutzroeder/netron)！Netron 是一款開源的 Neural Network 視覺化工具，他可以針對非常多的 Deep Learning 框架所設計出來的 Neural Network 進行視覺化，包含 ONNX、TensorFlow Lite、Caffe、Keras ... 等等，但是對於我們較為熟悉的 PyTorch 和 TensorFlow 則仍然處於實驗階段。

對於筆者自己的使用情況而言，覺得 Netron 對於 ONNX 的相容性最好，最不容易報錯。因此每當我想要將一個 Neural Network 視覺化時，我就會先將其轉為 ONNX 格式，再透過 Netron 將其視覺化！

下圖為將一個 ONNX 檔案透過 Netron 視覺化的結果：（也可以透過此[連結](https://netron.app/?url=https://media.githubusercontent.com/media/onnx/models/main/vision/classification/squeezenet/model/squeezenet1.0-3.onnx)開啟）

{{< image src="onnx-example.png" caption="Visualize ONNX in Netron" >}}

## ONNX Profile & Shape Inference

本文的主角不是 Netron，而是另一款筆者覺得好棒的 ONNX 工具 —— [onnx-tool](https://github.com/ThanatosShinji/onnx-tool)。沒錯！他的名字就是這麼的樸實無華，就是一個「ONNX 工具」。

每當我在透過 [Netron](https://github.com/lutzroeder/netron) 將 ONNX 視覺化時，我經常希望 Netron 除了可以顯示模型一開始和最後的 Tensor 的 Shape 之外，我也希望他可以把所有 Operation 的輸出的 Shape 都顯示出來。

如下圖所示：

{{< image src="onnx-example-2.png" caption="(左) 僅顯示模型一開始與最後的 Shape；(右) 顯示所有 Operation 的 Shape" >}}

如果要讓 Netron 把所有 Shape 都顯示出來，就必須確保 ONNX 檔案中有紀錄每一個 Operation 輸出的 Shape 的資訊。為了達到這樣的目的，我們需要對 ONNX 模型進行「Shape Inference」。ONNX 官方也有提供一個簡單的 Shape Inference 範例。然而，這個方法卻有一些限制：針對 Reshape 或是 Concat 等動態產生的 Shape，在官方的 Shape Inference 方法中就無法處理。

而 [onnx-tool](https://github.com/ThanatosShinji/onnx-tool) 的 Shape Inference 功能就能夠處理這樣的問題！ [onnx-tool](https://github.com/ThanatosShinji/onnx-tool) 除了能夠進行 Shape Inference 外，也能進行 Profile：

{{< image src="onnx-profile.png" caption="針對 ONNX 進行 Profile" >}}

透過 Profile 功能，我們可以知道每一個 Operation 或是整個 Model 的參數量 (Params)、運算量 (MACs) 以及輸入與輸出的形狀。除了 Shape Inference 與 Profile 外，[onnx-tool](https://github.com/ThanatosShinji/onnx-tool) 還有很多好用的功能，就等著讀者自己去探索囉！

## 結語

在本篇文章中，我們介紹了一款好用的 [ONNX 工具](https://github.com/ThanatosShinji/onnx-tool)，透過它簡單的對 ONNX 進行 Shape Inference 與 Profile。搭配 [Netron](https://github.com/lutzroeder/netron) 來視覺化 ONNX，可以讓你更全面的了解你的模型！如果你不曾聽過 ONNX，可以參考此篇[文章](https://ithelp.ithome.com.tw/articles/10210800)來對其有一個基本瞭解。
