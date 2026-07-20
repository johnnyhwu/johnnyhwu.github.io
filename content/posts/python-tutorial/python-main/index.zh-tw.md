---
# weight: 1
title: "一篇搞懂 Python 的 if __name__ == \"__main__\"：模組化與執行的關鍵"
date: 2022-06-17
lastmod: 2025-11-01
draft: false
description: "一篇搞懂 Python 中的 if __name__ == \"__main__\"！本篇教學將深入解析 __name__ 變數的意義，讓你了解為何它是編寫可重用模組與可執行腳本的關鍵，並學會如何避免程式碼在被引入 (import) 時意外執行。"
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

在 [Python Module 觀念解析](../python-module/)中，我們清楚的介紹了 Python 中 Module 的觀念。在開始閱讀本篇文章之前，一定要先了解 Python 中 Module 的觀念！當我們對 Python 的基本語法愈來愈熟悉時，我們時常會將別人寫好的 Module 引入到我們的程式中，我們開始會觀察到一件事情，許多人會在 Module 檔案中寫上：

```python
if __name__ == "__main__":
    # 程式碼
```

為什麼不直接寫程式碼就好，還要特別將程式碼包在 **if \_\_name\_\_ == "\_\_main\_\_":** 的判斷之下呢？這個判斷又有什麼意義呢？

## 建立一個 Module (tool.py) 與主程式 (main.py)

首先，我們一樣在 Colab 中建立一個 Module (`tool.py`)，並在這個 Module 中寫上以下的程式碼：

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
def func1():
    print("In func1")

def func2():
    print("In func2")

print("in tool.py")

```

此外，我們在 Colab 中新增另外一個檔案 (`main.py`) 作為我們主程式 (Main Program)，並貼上以下程式碼：

```python {open=true, lineNos=false, wrap=false, header=true, title="main.py"}
import tool

tool.func1()
tool.func2()
```

結果如下圖所示：

{{< image src="demo-1.png" alt="Colab 編輯器開啟 main.py，內容為 import tool 並呼叫 tool.func1() 與 tool.func2()，旁邊可看到 tool.py 分頁" caption="在 Colab 中新增 `tool.py`" >}}

接著，我們在 Colab 的程式碼區塊執行以下指令：

```bash
!python main.py
```

這個指令表示我們透過 Python 的直譯器 (Interpreter) 來執行 `main.py` 這個 Python 程式。如果不了解什麼是 Python Interpreter 也沒有關係，只需要知道就是在告訴電腦執行這個 Python 程式。 執行後，將會得到以下結果：

```text
in tool.py
In func1
In func2
```

相信學完 [Python 函式 (Function) 觀念](../python-function/)後，你一定相當清楚為什麼會有「In func1」與「In func2」的輸出。然而，對於為什麼會有「in tool.py」的輸出呢？讓我們繼續看下去！

## Python 在引入 Module 時做了什麼事情

在執行 `main.py` 這個程式時，首先被執行的是「import tool」這行程式碼：

```python {open=true, lineNos=false, wrap=false, header=true, title="main.py"}
import tool

tool.func1()
tool.func2()

```

在 Python 程式中，當電腦在執行「引入 Module」的程式碼時，實際上發生了兩件事情：

1.  電腦會替這一個 Module 建立一些特別的變數（例如：**\_\_name\_\_**）
2.  電腦會去執行 Module 中的每一行程式碼

以上述的 `main.py` 為例，當我們在執行 `main.py` 時，電腦首先會執行到「import tool」這行程式碼。此時，就會替 tool Module 設定一些特別的變數（例如： \_\_name\_\_），並執行 tool Module 中的每一行程式碼。 當電腦在執行 tool Module 中的每一行程式碼時：

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
def func1():
    print("In func1")

def func2():
    print("In func2")

print("in tool.py")

```

除了定義兩個 Function 外，也會在最後 `print("in tool.py")`。 現在問題來了，我們在 `main.py` 中引入 tool Module，其實只是想使用 tool Module 中定義的 `func1()` 與 `func2()` 並不希望執行 tool Module 最後的「`print("in tool.py")`」，這時候我們就可以透過下方這句神奇的判斷語句，達到我們的目的：

```python
if __name__ == "__main__":
    # 程式碼
```

## 透過 `dir()` 查看 Module 中所有定義的名稱

在理解這段神奇的判斷語句到底是什麼意思之前，我們先理解「**\_\_name\_\_**」究竟是什麼。 如同上面所提到的，在 Python 程式中，當電腦在執行「引入 Module」的程式碼時，實際上發生了兩件事情：

1.  電腦會替這一個 Module 建立一些特別的變數（例如：**\_\_name\_\_**）
2.  電腦會去執行 Module 中的每一行程式碼

我們可以看看電腦到底替 Module 設定了哪些特別的變數，我們必須在 `main.py` 新增一行程式碼 `print(dir(tool))`，因此 `main.py` 會長的像這樣：

```python {open=true, lineNos=false, wrap=false, header=true, title="main.py"}
import tool

print(dir(tool))

tool.func1()
tool.func2()
```

接著，在 Colab 中再次執行以下指令，讓電腦來執行 `main.py` 這個程式：

```bash
!python main.py
```

我們會得到以下的輸出：

```text
in tool.py
['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'func1', 'func2']
In func1
In func2
```

第二行輸出就是表示 tool Module 中所有被定義的名稱，除了「func1」與「func2」是我們定義的，其他都是電腦在「import tool」時自動幫我們定義的。

## 了解 \_\_name\_\_ 的值是什麼

「\_\_name\_\_」這一個變數我們可以想成是這一個 Module、這一個 Python 檔案的名字。\_\_name\_\_ 變數中的值可以分為以下兩種：

*   當這一個 Module、這一個 Python 檔案是直接被執行的時候，則 **\_\_name\_\_ 設為 "\_\_main\_\_"**
*   當這一個 Module、這一個 Python 檔案是被引入的時候，則 **\_\_name\_\_ 設為「檔案名稱」**

舉例來說，我們在 `tool.py` 的最前面再新增一行程式碼，來顯示 `tool.py` 的 \_\_name\_\_：

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
print(f"tool.py __name__: {__name__}")

def func1():
    print("In func1")

def func2():
    print("In func2")

print("in tool.py")
```

接著，我們回到 Colab 編輯器中，執行以下指令來執行 `main.py`：

```bash
!python main.py
```

會得到以下輸出：

```text
tool.py __name__: tool
in tool.py
['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'func1', 'func2']
In func1
In func2
```

我們可以發現**當 tool Module 是被引入時，它的 \_\_name\_\_ 會是它的檔案名稱**。 接著，我們回到 Colab 編輯器中，執行以下指令來執行 `tool.py`：

```bash
!python tool.py
```

會得到以下輸出：

```text
tool.py __name__: __main__
in tool.py
```

我們可以發現**當 tool Module 是被直接執行時，它的 \_\_name\_\_ 會是 "\_\_main\_\_"**。

## 透過 if \_\_name\_\_ == "\_\_main\_\_": 避免 Module 中的部分程式碼在「被引入」時執行

相信你已經很清楚 \_\_name\_\_ 是什麼以及它的值會是什麼。最後，如果我們希望 `main.py` 在引入 tool Module 時，tool Module 中的某些程式碼不要被執行，我們就可以將這些程式碼放在「if \_\_name\_\_ == "\_\_main\_\_"」之下：

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
print(f"tool.py __name__: {__name__}")

def func1():
    print("In func1")

def func2():
    print("In func2")

if __name__ == "__main__":
    print("in tool.py")
```

在 Colab 中再次執行以下指令，讓電腦來執行 `main.py` 這個程式：

```bash
!python main.py
```

得到以下輸出：

```text
tool.py __name__: tool
['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'func1', 'func2']
In func1
In func2
```

耶！「in tool.py」不見了。

## 結語

在本篇文章中，我們介紹了 Module 的 \_\_name\_\_ 是什麼，以及 \_\_name\_\_ 中存的值的規則。最後，我們也介紹到如何透過 if \_\_name\_\_ == "\_\_main\_\_": 避免 Module 中的部分程式碼在「被引入」時執行。
