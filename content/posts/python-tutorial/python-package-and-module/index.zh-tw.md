---
# weight: 1
title: "告別雜亂的 Python 專案！一次學會用 Package 有效管理你的程式碼"
date: 2022-06-19
lastmod: 2025-11-01
draft: false
description: "什麼是 Python Package？本文用最簡單的比喻「Module 是檔案，Package 是資料夾」帶您入門，了解 __init__.py 的用途，並透過實際範例，學習如何有效組織您的 Python 專案程式碼。"
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

在 [Python Module 觀念解析](../python-module/)一文中，我們介紹了 Python 中 Module 的觀念，了解所謂的 Python Module 其實就是一個包含許多「可重複使用」的程式碼的 Python 檔案。基於我們對 Python Module 的理解，我們解釋了 [Python 中 if \_\_name\_\_ == \_\_main\_\_ 有什麼用處](../python-main/)。 在本篇文章中，我們將介紹 Python 中的 Package 是什麼。如果說 Python Module 是一個 Python 檔案的話，那麼 **Python Package 其實就是一個裝有很多 Python 檔案的資料夾**。讓我們繼續看下去，理解 Python Package 是什麼以及其用法。

## Python Package 是什麼

在我們自己電腦的相片集中，我們不會將所有的相片通通塞在一個資料夾裡面，我們可能會根據相片的日期或地點，將同性質的相片放在同一個資料夾中。同樣的，當我們今天寫的 Python 程式是一個大型專案，整個專案中包含了非常多的 Python 檔案 (Module)，我們不會將所有的 Python 檔案都放置在同一個資料夾中，而是會依照功能目的將 Python 檔案放置在不同的資料夾中：

{{< image src="project-structure.png" caption="一個專案底下 Python 檔案的結構 (source: www.programiz.com)" >}}

上圖呈現的是一個範例，在 Game Package 底下有三個 Package，每一個 Package 中都包含許多 Module。由上圖的範例中，我們也可以發現每一個 Package 底下都有一個「**\_\_init\_\_.py**」檔案，這個檔案中不需要撰寫任何程式碼。這個檔案是為了讓電腦**把這一個資料夾視為一個 Python Package，而不是普通的資料夾**！

## Python Package 範例

接著，讓我們實際建立一個 Python Package 演練一下吧!

首先在 Colab 中新增一個資料夾「project」，為了要讓這一個資料夾成為一個 Python Package，我們要在底下新增一個「\_\_init\_\_.py」。此外，我們也再新增一個「main.py」。如此一來，「project」底下的檔案如下圖所示：

{{< image src="demo-1.png" caption="project 底下包含 \_\_init\_\_.py 與 main.py" >}}

此外，我們在 project 底下新增另外一個 Package「tools」。同樣的，為了要讓 tools 資料夾也成為一個 Python Package，我們在 tools 底下新增一個「\_\_init\_\_.py」。此外，我們再新增一個「tool.py」。如此一來，「project」底下的檔案如下圖所示：

{{< image src="demo-2.png" caption="在 project package 底下新增一個 tool package" >}}

我們在「too.py」中新增一個 Function，能夠將兩個數字加總並乘以第三個數字：

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
def sum_mul(a, b, c):
    return (a+b)*c
```

在「main.py」中新增以下這段程式碼，從 tools Package 中引入 tool Module，並使用 tool Module 中的 Function：

```python {open=true, lineNos=false, wrap=false, header=true, title="main.py"}
from tools import tool
print(tool.sum_mul(1, 2, 3))
```

最後，我們在 Colab 編輯器中執行以下指令，讓電腦執行 main.py：

```bash
!python ./project/main.py
```

從輸出可以發現 main.py 成功使用 tools Package 中的 tool Module 中所定義的 Function。 當然，要如何引入 Package 中的 Module，或是 Module 中所定義的元素，可以參考 [Python Module 觀念解析](../python-module/)一文中，我們所介紹的 4 種方法。

## 結語

在本篇文章中，我們介紹了 Python Package 的概念。簡單來說，**如果 Python Module 是一個 Python 檔案，那麼 Python Package 就是一個包含很多 Python 檔案的資料夾。**
