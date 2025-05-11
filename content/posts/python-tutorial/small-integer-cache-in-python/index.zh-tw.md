---
# weight: 1
title: "Python 中的 Integer Cache 介紹"
date: 2024-10-03
lastmod: 2024-10-03
draft: false
description: "深入探索 Python 的 Small Integer Cache 機制！了解 Python 如何透過預先配置 [-5, 256] 範圍內的整數物件以優化記憶體、提升執行效率。本文將搭配 id()、Reference Count 及 REPL 與檔案執行的差異進行說明"
featuredImage: "featured-image.png"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

率，而且已經被實做在 Python 中。

本篇文章適合對於 Python 程式語言已經有基本認識，且希望學習一些 Python 的底層知識的讀者！如果你還是一名程式初學者，並且想從 Python 開始學習的話，可以參考 [Python 教學系列文章](https://datasciocean.tech/categories/python-tutorial/)。

## Small Integer Cache

為了體現 Python 中 Small Integer Cache 的概念，我們可以先看看以下程式碼執行的結果：

```bash
Python 3.12.5 | packaged by Anaconda, Inc. | (main, Sep 12 2024, 18:27:27) \[GCC 11.2.0\] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> a = 100
>>> b = 100
>>> print(id(a) == id(b))
True
>>> c = 257
>>> d = 257
>>> print(id(c) == id(d))
False
>>>
```

在 Python 中，我們可以透過 [id()](https://www.digitalocean.com/community/tutorials/python-id) 函式來取得一個物件 (Object) 的 Memory Address。

因此，從上面的執行結果可以發現 a 和 b 明明是不同的兩個變數，但是他們的 Memory Address 卻一樣，而 c 和 d 的 Memory Address 又相同？！ 會發生上面的狀況主要是 Python 語言的實做中包含了 **Integer Cache** 的機制：

{{< image src="integer-cache.png" caption="Integer Cache from Python Document" >}}

如上圖所示，從 [Python 的官方文件](https://docs.python.org/3/c-api/long.html#c.PyLong_FromLong)中我們可以發現：對於一些**比較常見的 Integer [-5, 256]**，Python 會**事先建立 (Pre-Allocated) 這些 Integer 的 Object**，當我們在程式碼中宣告的 Integer 在這個範圍時，其實都會 Reference 到同一個 Object 而不會建立新的 Object。

這也就清楚的說明了，為什麼在上面的程式執行結果上，變數 a 和 b 會指到同一個 Memory Address 而變數 c 和 d 則是指到不同的 Memory Address。這個 Integer Cache 的目的當然是為了讓 Python 程式的運作更有效率，針對比較常出現在程式中的 Integer，減少做 Memory Allocation 的次數。

## Reference Count

為了說明 [-5, 256] 這個區間的 Integer 確實比較常被使用到，我們也可以印出這些 Integer Object 的 **Reference Count**。所謂的 Reference Count 是指一個 Object 被 Reference 到的次數。 更具體的來說，以 CPython 所實做的 Python 版本為例，[Integer 在 CPython 中的表示會是](https://hg.python.org/cpython/file/3.4/Include/longintrepr.h/#l89)：

```c
struct _longobject {
    PyObject_VAR_HEAD
    digit ob_digit[1];
};
```

其中，從 [Python 官方文件](https://docs.python.org/3/c-api/structures.html#c.PyObject_VAR_HEAD)我們可以看到 PyObject_VAR_HEAD 這個 Macro 其實是表示：

```c
PyVarObject ob_base;
```

再回到 [CPython 的原始碼中](https://hg.python.org/cpython/file/3.4/Include/object.h#l111)，我們可以發現 PyVarObject 其實就是[把 PyObject 再加上一個 ob_size 的欄位](https://docs.python.org/3/c-api/structures.html#c.PyVarObject)：

```c
typedef struct _object {
    _PyObject_HEAD_EXTRA
    Py_ssize_t ob_refcnt;
    struct _typeobject *ob_type;
} PyObject;

typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size; /* Number of items in variable part */
} PyVarObject;
```

因此，最終一個 Integer Object 在 Python 中其實會是：

```c
struct _longobject {
    long ob_refcnt;
    PyTypeObject *ob_type;
    size_t ob_size;
    long ob_digit[1];
};
```

`ob_refcnt` 就是表示這個 Integer Object 的 Reference Count！在 Python 中我們可以透過 `sys.getrefcount()` 函式來取得一個 Object 的 Reference Count，並透過一些繪圖套件 (ex. [matplotlib](https://matplotlib.org/)) 呈現這些 Integer Object 被 Reference 到的次數分佈：

{{< image src="reference-count.png" caption="Reference counts of interger values" >}}

可以發現到在還沒有加入自己的其他 Code  之前，光是 Python Interpreter/Compiler 內部的運作就已經對這些 Smaller Integer 做了很多次 Reference。透過 Integer Cache 的機制確實可以減少對這些經常用到的 Integer Object 做 Memory Allocation。

## Python REPL vs Python File

在上述的程式碼範例中，是在 [Python REPL](https://python.land/introduction-to-python/the-repl) 或是 [Python Shell](https://www.python.org/shell/) 環境中進行的。如果我們先將程式碼打在一個 Python File (ex. main.py) 中，再透過 `python main.py` 的方式執行，會發現不管針對什麼範圍的 Integer，只要是相同的 Integer，兩個變數的 Memory Address 就會是一樣的。

這是因為當我們透過 python main.py 執行程式碼時，Python 中的 Compiler 其實已經可以先針對所有的 Code 做分析並且優化，當它發現到我們有兩個 Integer Object 的數值其實是一樣的時候，就會讓它們 Reference 到相同的 Object，來減少 Memory 的浪費。 而在 Python REPL 環境中，因為 Python 的 Compiler 每一次都只能讀取一行 Code，因此在優化上就會有所限制，而將 Integer Cache 的機制赤裸裸的呈現。

## 結語

本篇文章中我們介紹了Python 中的 Integer Cache 機制是如何作用在 [-5, 256] 範圍的 Integer 上，同時透過 CPython 的原始碼來說明這些 Integer Object 的 Reference Count。

## 參考資料

- [Python Object Caching - How does Python Optimize Memory Management for Integers?](https://micahondiwa.hashnode.dev/python-object-caching-how-does-python-optimize-memory-management-for-integers)
- [Python Official Document - Common Object Structures](https://docs.python.org/3/c-api/structures.html#c.PyObject)
- [Python Official Document - Integer Objects](https://docs.python.org/3/c-api/long.html)
- [Python Caches Integers](https://www.codementor.io/@arpitbhayani/python-caches-integers-16jih595jk)
- [Why Python is Slow: Looking Under the Hood](https://jakevdp.github.io/blog/2014/05/09/why-python-is-slow/)
- [Python cached integers](https://thepythoncorner.com/posts/2022-06-18-the-sunday-tip-1-python-cached-integer/)
- [Python WAT!? Integer Cache](https://wsvincent.com/python-wat-integer-cache/)
- [What's with the integer cache maintained by the interpreter?](https://stackoverflow.com/questions/15171695/whats-with-the-integer-cache-maintained-by-the-interpreter)
- [Why python integer caches range \[-5, 256\] don't work in similar way on all platform?](https://stackoverflow.com/questions/63188021/why-python-integer-caches-range-5-256-dont-work-in-similar-way-on-all-platf)