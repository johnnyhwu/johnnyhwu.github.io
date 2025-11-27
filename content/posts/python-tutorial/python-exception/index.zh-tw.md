---
# weight: 1
title: "Python 錯誤處理入門：學會用 try 和 except 讓程式不再閃退"
date: 2022-05-22
lastmod: 2025-11-27
draft: false
description: "還在為 Python 程式遇到 Error 就崩潰而煩惱嗎？本篇初學者教學將帶你入門 Python 的錯誤處理，學習如何使用 try、except 與 pass 來捕捉並處理錯誤，讓你的程式碼更穩定，不再輕易停止執行。"
featuredImage: "featured-image.png"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

## 前言

在學習如何處理 Python 程式中發生的 Error 之前，只要 Python 程式執行到一半發生 Error，整個程式就會停止 (Crash)，不會再繼續執行，這是我們不希望發生的結果。因此，在本篇文章中，我們將學習如何處理 Python 程式中的 Error，讓程式即使遇到 Error 也不至於整個停止執行。

## 為什麼要處理 Python 程式中的 Error

在開始學習如何處理 Python 程式中的 Error 之前，我們先了解為什麼要這麼做。 想像現在老闆要你寫一個 Python 程式，不停地接受使用者輸入數字，並告訴使用者這一個數字的「倒數」。使用者會在程式印出結果之後，就輸入下一個數字：

*   使用者輸入 16 → 程式印出 0.0625 (1/16)
*   使用者輸入 20 → 程式印出 0.05 (1/20)
*   使用者輸入 25 → 程式印出 0.04 (1/25)
*   使用者輸入 30 → 程式印出 0.0333 (1/30)
*   ...

依照老闆這樣的需求，你馬上回想到之前學過[迴圈 (Loop) 的觀念](../python-loop/)，學過[函式的用法](../python-function/)，而寫出了下面這段程式碼：

```python
while True:
    inp = input("數字: ")
    inp = int(inp)
    print(f"倒數: {1/inp}")
    print()
```

「這段程式碼看起來運作的非常正常」你滿懷得意的這麼想！ 然而，有一天一個使用者手滑不小心輸入「數字 0」(我們知道 0 不能放在分母，當然不能計算它的倒數) ... 當你的程式再計算 `1/0` 等於多少時，跳出了 Error：

{{< image src="exception.png" caption="Python 中的 Error 範例" >}}

然後，它就沒有繼續接受使用者的輸入了 (你的老闆鐵定氣炸了) ！ 這就是為什麼我們要學習如何處理 Python 程式中的 Error，它讓我們可以在程式「執行時」遇到 Error 時，整個程式不會停止掉。

## Python 中的 `try` 與 `except`

在 Python 中，我們可以透過 **try** 與 **except** 關鍵字，來處理 Python 程式中的 Error。我們將「可能發生 Error」的程式碼放在 try 之中，將如果真的發生 Error 應該做什麼事情的程式碼放在 except 之中。 以剛剛的程式為例，我們應該將計算倒數的程式碼放在 try 之中，並在 except 之中告訴使用者不應該輸入 0：

```python
while True:
    inp = input("數字: ")
    inp = int(inp)

    try:
        print(f"倒數: {1/inp}")
    except:
        print("不應該輸入 0")
    
    print()
```

如此一來，即使使用者不小心輸入 0，使得 `1/inp` 發生 Error 時，電腦會自動去執行 except 中的程式碼。執行完 except 中的程式碼後，再繼續執行原來的程式碼。

## Python 中的 `pass`

我們已經知道透過 try 與 except 語法，當程式發生 Error 時，電腦會去執行 except 之中的程式碼。那如果我們希望程式在執行中發生了 Error，電腦並不需要特別做什麼事情，只需要繼續執行剩下的程式時，這時該怎麼做呢？

以前面老闆要你寫的程式為例，假設你不希望程式在使用者輸入數字 0 後，做任何的事情，只需要忽略這筆輸入，繼續接受下一筆輸入即可，那我們可以怎麼做呢？ 最直覺的想法，就是直接把 except 拿掉：

```python
while True:
    inp = input("數字: ")
    inp = int(inp)

    try:
        print(f"倒數: {1/inp}")
print()
```

然而，這樣的語法在 Python 中是錯誤的！因為**只要出現了 try ，後面至少要接一個 except**。 因此，我們可以透過 **pass** 關鍵字：

```python
while True:
    inp = input("數字: ")
    inp = int(inp)

    try:
        print(f"倒數: {1/inp}")
    except:
        pass
print()
```

`pass` 的意思就是字面上的意思，就是不需要做任何事情！

## 結語

在本篇文章中，我們了解到為什麼要處理 Python 中的 Error，以及如何透過 `try`, `except` 與 `pass` 來達到目的！
