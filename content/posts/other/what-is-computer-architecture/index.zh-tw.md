---
# weight: 1
title: "別再搞混！一篇文搞懂「計算機結構」與「計算機組織」的差別"
date: 2023-06-22
lastmod: 2025-10-16
draft: false
description: "搞不懂計算機結構 (Computer Architecture) 與計算機組織 (Computer Organization) 的差別？本篇文章將用淺顯易懂的方式，帶你了解計算機結構如何扮演軟體與硬體的關鍵橋樑，並解析指令集架構 (ISA) 的核心概念。"
featuredImage: "featured-image.png"

tags: ["Computer Architecture"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

本篇文章是一篇 [ELE 475 Computer Architecture](https://www.coursera.org/learn/comparch) 的修課筆記！因此本篇文章中的插圖，主要也是來自於這門課程的投影片。 本篇文章主要是以一個很宏觀的角度來簡單說明 Computer Architecture 到底在 Computer System 中扮演什麼角色，和 Computer Organization 的差別是什麼，最後則會提到 Computer Architecture 中會包含什麼資訊。

## Computer Architecture 所扮演的角色

Computer Architecture 也算是資工系學生必修課程之一，但學完了一整學期的課程，你真的清楚 Computer Architecture 在整個 Computer System 所扮演的角色是什麼嗎？

下方這張圖很好的解釋了 Computer Architecture 的任務：

{{< image src="def.png" alt="示意圖中一支垂直大箭頭連接上方的 Application 方塊與下方的 Physics 方塊，標註兩者差距太大無法一步跨越，旁邊的定義說明計算機結構設計出讓應用能在製造技術上有效執行的抽象與實作層" caption="Computer Architecture 所扮演的角色" >}}

我們想在「應用程式」中實現的事情該怎麼和最底層的「物理」概念結合在一起，中間勢必要經過很多層技術的轉換和抽象化，而 Computer Architectur 正是扮演著搭起 Application 與 Technology 的橋樑！

更精確地來說：

{{< image src="component.png" alt="從 Application 到 Physics 的抽象層堆疊，以括號標示中間的 Instruction Set Architecture、Microarchitecture 與 Register-Transfer Level 為計算機結構所涵蓋的範圍" caption="Computer Architecture 負責的任務" >}}

Computer Architecture 負責的是「Instruction Set Architecture」、「Microarchitecture」與「Register-Transfer Level」，在 Computer Architecture 之上的技術偏向軟體層面，在 Computer Architecture 之下的技術偏向硬體層面。

當硬體的技術進步時（例如，可以在一塊晶片上裝入更多的電晶體），就需要有更好的 Computer Architecture 來釋放技術進步所帶來的效能；當軟體層面想要加速一些特定的運算時（例如：加快 Video Processing 的計算），就需要 Computer Architecture 設計特定的 Instruction 達到此目的。

因此，位居 Computer System 中間橋樑的 Computer Architecture 可以說是同時的影響了軟體與硬體的發展，扮演著重要的角色！

## Computer Architecture vs Computer Organization

說到 Computer Architecture 經常會和另外一個領域「Computer Organization」搞混！尤其在大學裡，這兩個名詞剛好屬於兩個不同的課程，經常會讓同學傻傻分不清。在這裡用一個相對簡單的角度來解釋兩者的區別。我們先從認識他們的別名開始：

*   Computer Architecture = Architecture = Instruction Set Architecture
*   Computer Organization = Organization = Microarchitecture

以下我們用 Instruction Set Architecture 表示 Computer Architecture；用 Microarchitecture 表示 Computer Organization！ 
所謂的 Instruction Set Architecture 是以 **Software Engineer** 的角度來說明一個 Processor 的設計。對於 Software Engineer 來說，我只在乎這個 Processor 可以支援什麼樣的 Operation, Data Type 與 Data Size。

因此，在 Instruction Set Architecture 中，就會定義很多這個 Processor 可以支援的 Instruction，所有這些 Instruction 大致可以分為三種類型：

- Arithmetic/Logic Instruction
- Data Transfer Instruction
- Branch and Jump Instruction

此外，還會定義這些 Instruction 的長度（例如：32 Bits）。 

在 Microarchitecture 中，則是以 **Hardware Engineer** 的角度來說明一個 Processor 的設計。對於 Hardware Engineer 來說，我只在乎這個 Processor 實際上的硬體元件應該怎麼設計，才能支援 Instruction Set Architecture 中所定義的 Instruction。

因此，在 Microarchitecture 中，就會去設計這個 Processor 能不能做 Instruction Pipelining、Branch Prediction 或是 Out of Order Execution。

因此，Instruction Set Architecture 說明了這個 Processor 可以支援的 Operation，而 Microarchitecture 則是實作上的一些細節！

換句話說，一種 Instruction Set Architecture 可以有多種 Microarchitecture，有些 Microarchitecture 在意的是 Processor 的速度，有些在意的是成本（下圖就是一個例子）。

舉例來說，x86 是 Intel 提出的一種 Instruction Set Architecture，Intel 每年所推出不同世代的 Processor 就是使用相同的 Instruction Set Architecture 但為不同的 Microarchitecture，使得這些 Processor 的速度可以愈來愈快！而一個 Program (這裡指的是被 Compile 成 Machine Code 的狀態) 可以被一個 Instruction Set Architecture 為 x86 的 Processor 執行，就可以被其他所有同樣的 Instruction Set Architecture 的 Processor 所執行！

{{< image src="isa.png" alt="AMD Phenom X4 與 Intel Atom 的晶片照片比較，兩者都採用 x86 指令集但規格差異極大：Phenom 為四核心、亂序執行、125W、2.6GHz，Atom 為單核心、循序執行、2W、1.6GHz" caption="Same ISA but different microarchitecture" >}}

## Instruction Set Architecture 中的基本資訊

如同上面所說的，Instruction Set Architecture 是以 Software Engineer 的角度來描述一個 Processor，述說著這個 Processor 究竟支援著什麼 Instruction！Instruction Set Architecture 中的基本資訊不外乎：

*   **Instruction Type**：將所有 Instruction 分成數個種類
*   **Addressing Mode**：可以透過哪些方式從 Memory 讀取 Data
*   **Data Type and Size**：Data 的類型以及寬度
*   **Instruction Encoding**：Instruction 的寬度以及每一個 Byte 所代表的意義

首先，Instruction Set Architecture 裏頭會將所有 Instruction 分門別類。如下圖所示，有些 Instruction 用於傳遞資料 (例如：Load、Store)，有些用於數學運算 (例如：ADD、SUB)，也有些用於流程控制 (例如：Branch If Equal to Zero)。

{{< image src="isa-kind.png" alt="指令類型的條列清單與範例：資料傳輸、ALU、控制流程、浮點運算、多媒體 SIMD 與字串指令" caption="Instruction 可以分成多種類型" >}}

除此之外，也會清楚定義可以支援的 Addressing Mode，也就是可以用什麼方式從 Memory 中讀取 Data。比較特別的是，並不一定都是需要從 Memory 中讀取 Data，像是 Register Addressing Mode 就只需要從 Register 讀取 Data：

{{< image src="isa-type.png" alt="定址模式的表格，每一列給出一個 Add 指令範例與其意義，涵蓋暫存器、立即值、位移、暫存器間接、絕對、記憶體間接、PC 相對與縮放定址" caption="ISA 中也會定義清楚 Processor 可以支援的 Addressing Mode" >}}

說到讀取 Data，Instruction Set Architecture 也會清楚地義這個 Processor 所支援的 Data Type 以及 Size：

{{< image src="isa-width.png" alt="資料型別的清單，如二進位整數、BCD、浮點數 (IEEE 754、Cray、Intel 80-bit 擴充精度)、封裝向量與位址，以及各自支援的位元寬度" caption="ISA 也會定義 Data Type 與 Size" >}}

既然 Data 有 Size，Instruction 本身當然也 Size！從下圖中我們可以發現，Reduced Instruction Set Computer 系列的 ISA 通常是屬於 Fixed Width，也就是每一個 Instruction 的寬度都相同。

例如：MIPS ISA 中所有的 Instruction 都是 32 Bits。 而 Complex Instruction Set Computer 系列的 ISA 通常是屬於  Variable Length，也就是 Instruction 的長度是可以動的。例如，x86 ISA 中 Instruction 的長度從 1 Byte 到 17 Byte 都有。

{{< image src="isa-size.png" alt="指令寬度方案的整理：RISC 指令集 (如 MIPS) 採固定寬度、CISC 指令集 (如 x86，1 到 17 位元組) 採可變長度、Thumb 等採大多固定或壓縮，以及超長指令字 (VLIW) 的捆綁方式" caption="不同的 ISA 裡頭的 Instruction Size 也都不同" >}}

## 結語

在本篇文章中，我們了解到 Computer Architecture 在 Computer System 中扮演至關重要的「橋樑」位置，也明白其與 Computer Organization 的差別（Software Engineer's Perspective vs Hardware Engineer's Perspective）。最後，我們也了解到 Instruction Set Architecture 中會包含什麼樣的資訊！