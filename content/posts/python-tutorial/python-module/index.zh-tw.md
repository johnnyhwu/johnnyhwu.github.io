---
# weight: 1
title: "一篇搞懂 Python Module (模組)：從建立到 import，寫出可重複利用的乾淨程式碼"
date: 2022-06-17
lastmod: 2025-12-01
draft: false
description: "一篇搞懂 Python Module (模組)！本篇教學將帶你了解 Python 模組是什麼、如何建立自己的模組來封裝可重複使用的程式碼，並詳細解說 4 種 import 方式的差異與最佳實踐，讓你的程式碼更簡潔、更有效率。"
featuredImage: "featured-image.jpg"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

## 前言

在 [Python 中的函式 (Function) 觀念 (Part 1)](../python-function-1/)、[Python 中的函式 (Function) 觀念 (Part 2)](../python-function-2/) 與 [Python 中的函式 (Function) 觀念 (Part 3)](../python-function-3/) 中，我們透過三篇文章清楚的介紹了 Python 中函式 (Function) 的觀念。

透過 Function，我們可以讓我們撰寫的程式碼更有結構。舉例來說，當我們撰寫完某一個功能的 Python 程式碼時，我們可以將這段程式碼打包成一個 Function，如此一來，當我們要使用到這一個功能時，就只需要呼叫這一個 Function，而不需要重複撰寫程式碼。

實際上，Python 的強大之處正是有許多「現成工具」可以使用。也就是說，許多人已經將各種不同功能的 Python 程式碼寫好，當我們想要用某一個功能時，就只需要「引入」(Import) 相對應的「模組」(Module) 即可。

看到這裡，出現了兩個我們過去不曾見過的詞：Import 與 Module。在本篇文章，我們將會介紹 Python 中 Module 是什麼，以及如何建立一個 Module，徹底了解 Python 中 Module 的觀念。 如果你對於 Python Module 的觀念已經相當清楚，那麼你知道 [Python Module 與 Python Package 的差別](../python-package-and-module/)嗎？

## Python 中的 Module 是什麼

**Python 中的 Module 指的就是一個包含 Python 程式碼的檔案。** 例如，你在 Colab 中寫了一個 `example.ipynb` 或是 `example.py`，你就可以把它視為一個 Module，而這個 Module 的名稱就是「example」。

> 你可以會覺得驚訝，難道 Module 就這樣而已嗎？那我們平常寫的 Python 檔案都算是 Module 嗎？

沒錯！我們可以將一個包含有 Python 程式碼的檔案視為 Python Module，但是 Module 裡面的程式碼通常具有一個特性：**「可重複使用」**。

舉例來說，我們會將我們經常會用到的功能打包成許多個 Function，然後我們將這些 Function 放在一個 Python 檔案中，例如 `tool.py`。當我們在其他的程式，要使用到這些功能時，我們就可以 Import 這一個 Module，或是只有 Import Module 中的其中一個 Function。如此一來，我們就不用再重新寫一個一模一樣的 Function。

## 建立一個 Python Module

對於 Python 中的 Module 有一點認識之後，我們就來動手建立一個 Module。首先開啟 Colab 環境，並將這個 Colab 檔案命名為 `main.ipynb`，然後在左側檔案列表的區域，點擊右鍵後「新增檔案」：

{{< image src="colab.png" alt="Colab 檔案面板中開啟右鍵選單，顯示上傳、重新整理、新增檔案與新增資料夾等選項" caption="在 Colab 中新增檔案" >}}

我們將檔案命名為 `tool.py`，表示這一個 Module 的名稱為「tool」。 接著，打開 `tool.py` 並在裡頭打上以下這段程式碼：

```python
def sum_mul(a, b, c):
    return (a+b)*c
```

我們在 Module 中新增了一個 Function，這一個 Function 可以計算兩個數字的總和再乘以第三個數字。

## 引入 Module 並使用 Module 中的 Function

接著，我們要開始在我們目前的 Colab 檔案 (`main.ipynb`) 中撰寫程式，並使用 tool Module 裡面 Function。 然而，在 `main.ipynb` 中並不知道 tool Module 的存在，更不用說去使用 tool Module 中的 Function。因此，我們要透過 Python 中的**「import」** 關鍵字將 tool Module 引入到 `main.ipynb` 中：

```python
import tool
```

如此一來，`main.ipynb` 就知道 tool Module 的存在了。 `main.ipynb` 雖然知道 tool Module 的存在，但是不知道 tool Module 裡面有什麼 Function。因此，如果要使用 tool Module 中我們剛剛定義的 Function，就必須透過 `.` 這個特殊符號來使用：

```python
print(tool.sum_mul(1, 2, 3))
```

## 四種引入 Module 的方法

實際上，引入 Module 的方法有很多種，主要可以分為以下 4 種，讓我們一一理解他們。 **單純引入 Module** 第一種為單純引入一個 Module，並透過 `.` 來存取 Module 中的程式碼。

```python
import tool
print(tool.sum_mul(1, 2, 3))
```

**引入 Module 的同時賦予 Module 新的名字** 透過 `as` 關鍵字，給予 Module 新的名字，這樣在後面存取 Module 中的 Function 時，我們就可以不用打那麼多字。

```python
import tool as t
print(t.sum_mul(1, 2, 3))
```

**只引入 Module 中的某些元素** 有時候，我們並不想要引入整個 Module，因為我們只會用到 Module 中的一兩個元素。此時，我們就可以透過 `from` 關鍵字，引入 Module 中特定的元素。如此一來，在後方的程式碼我們就可以直接使用那些元素，而不需要透過 Module。

```python
from tool import sum_mul
print(sum_mul(1, 2, 3))
```

**引入 Module 中所有的元素** 如果一個 Module 中有很多元素（例如很多 Function），透過第 3 種引入方式想必會很費力。這時候我們可以透過 `*` 符號，將 Module 中所有的元素都引入。如此一來，在後方的程式碼我們同樣可以直接使用那些元素，而不需要透過 Module。

```python
from tool import *
print(sum_mul(1, 2, 3))
```

這邊有一個小提醒，通常我們不建議引入 Module 中所有的元素，這樣容易增加程式出錯的機率。 舉例來說，假設我們現在在 `main.ipynb` 中撰寫我們程式，我定義了一個 Function 稱為「sum_mul」：

```python
def sum_mul(a, b, c, d):
    return (a+b+c)*d
```

接著，我希望使用 tool Module 裡面的功能，因此我將 tool Module 中所有的元素都引入：

```python
from tool import *
```

這時候，我們再去使用我們剛剛所定義的 `sum_mul` Function 會發生什麼事情？

```python
sum_mul(1, 2, 3, 4)
```

```text
---------------------------------------------------------------------------
TypeError Traceback (most recent call last)
<ipython-input-14-ceb4a433275d> in <module>()
----> 1 sum\_mul(1, 2, 3, 4)

TypeError: sum\_mul() takes 3 positional arguments but 4 were given
```

我們發現 `sum_mul()` 沒有辦法正確被執行，因為他接受 3 個參數，我們卻傳了 4 個參數進去！會導致這樣的原因在於我們將 tool Module 中所有的元素引入的同時，tool Module 中的 `sum_mul()` Function「覆蓋」了我們原先定義的 `sum_mul()` Function。 因此，當我們在引入 Module 時，最建議的做法是「**單純引入 Module**」或「**引入 Module 的同時賦予 Module 新的名字**」兩種方法。

## Python 中的 Standard Module

Python 程式語言中有許多內建、事先建立好的好的 Module，我們可以在 [Python Module Index](https://docs.python.org/3/py-modindex.html) 中查看。[Python Module Index](https://docs.python.org/3/py-modindex.html) 中呈現的所有 Module，就是我們在自己的電腦上安裝 Python 程式語言時，會自動下載的 Module。

我們要使用這些 Module 時，只需要使用我們上面所提到的各種不同的引入方法，將 Module 引入到我們的程式中。舉例來說，Python 的 Standard Module 中有一個 `os` Module：

{{< image src="module.png" alt="Python Module Index 中以 o 開頭的模組列表節錄，包含 operator、optparse、os、ossaudiodev 等模組與簡短說明" caption="Python 中的 Standard Module" >}}

`os` Module 中定義了各種與作業系統相關的操作。例如，如果我們想要列出一個資料夾中的所有檔案，就可以使用 `os` Module 中的功能。

## 結語

在本篇文章中，我們介紹了 Python 中 Module 的觀念，了解所謂的 Python Module 其實就是一個包含許多「可重複使用」的程式碼的 Python 檔案。我們也介紹了 4 種引入 Python Module 的方法，其中最推薦「單純引入 Module」或「引入 Module 的同時賦予 Module 新的名字」，來避免程式執行時出現錯誤。

在[下一篇文章](../python-main/)中，我們將基於你對 Python Module 的理解，了解為什麼有些人會在 Python 檔案中寫上：

```python
if __name__ == "__main__":
```

這樣的程式碼呢？