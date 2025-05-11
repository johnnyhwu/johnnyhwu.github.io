---
# weight: 1
title: "Python's Small Integer Cache: Faster Code with a Hidden Trick"
date: 2024-10-03
lastmod: 2024-10-03
draft: false
description: "Discover Python's Small Integer Cache! Learn how Python optimizes common integers (-5 to 256) for faster performance and efficient memory use. Simple examples included."
featuredImage: "featured-image.png"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "python-tutorial/:contentbasename"
---

<!--more-->

## Introduction

This article aims to share a neat trick in the Python language known as the "Small Integer Cache." This trick is designed to boost the performance of Python programs and is already implemented within Python itself.

This piece is for readers who have a basic understanding of the Python programming language and are interested in learning some of Python's underlying mechanisms. If you're a programming beginner looking to start with Python, you might find our [Python Tutorial Series](https://datasciocean.tech/categories/python-tutorial/) helpful.

## Small Integer Cache

To demonstrate the concept of Python's Small Integer Cache, let's first look at the results of the following code execution:

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

In Python, we can use the `id()` function to get the memory address of an object.

Therefore, from the results above, you'll notice that `a` and `b`, although different variables, share the same memory address. However, `c` and `d` have different memory addresses. Why is this? This happens because Python's implementation includes an **Integer Cache** mechanism:

{{< image src="integer-cache.png" caption="Integer Cache illustration from Python's Official Documentation" >}}

As shown in the image from [Python's official documentation](https://docs.python.org/3/c-api/long.html#c.PyLong_FromLong), Python pre-allocates objects for commonly used integers, specifically those in the range of **-5 to 256**. When you declare an integer within this range in your code, Python will point to this pre-existing object instead of creating a new one.

This clearly explains why, in the code execution results above, variables `a` and `b` point to the same memory address, while variables `c` and `d` point to different ones. The goal of this Integer Cache is, of course, to make Python programs run more efficiently by reducing the number of memory allocations for frequently used integers.

## Reference Count

To further illustrate that integers in the -5 to 256 range are indeed frequently used, we can examine their **Reference Count**. The Reference Count is simply the number of times an object is referenced (or pointed to). More specifically, in the CPython implementation of Python, [an integer is represented in CPython as](https://hg.python.org/cpython/file/3.4/Include/longintrepr.h/#l89):

```c
struct _longobject {
    PyObject_VAR_HEAD
    digit ob_digit[1];
};
```

From the [Python official documentation](https://docs.python.org/3/c-api/structures.html#c.PyObject_VAR_HEAD), we can see that the `PyObject_VAR_HEAD` macro actually represents:

```c
PyVarObject ob_base;
```

Going back to [CPython's source code](https://hg.python.org/cpython/file/3.4/Include/object.h#l111), we find that `PyVarObject` is essentially [a `PyObject` with an added `ob_size` field](https://docs.python.org/3/c-api/structures.html#c.PyVarObject):

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

Thus, an integer object in Python ultimately looks like this:

```c
struct _longobject {
    long ob_refcnt;
    PyTypeObject *ob_type;
    size_t ob_size;
    long ob_digit[1];
};
```

`ob_refcnt` is the field that stores the Reference Count for the integer object. In Python, we can use the `sys.getrefcount()` function to get an object's Reference Count. We can then use plotting libraries (e.g., [matplotlib](https://matplotlib.org/)) to visualize the distribution of how many times these integer objects are referenced:

{{< image src="reference-count.png" caption="Reference counts of integer values" >}}

You'll notice that even before adding any custom code, the Python interpreter/compiler itself makes many references to these smaller integers. The Integer Cache mechanism genuinely helps reduce memory allocation for these commonly used integer objects.

## Python REPL vs. Python File

The code examples shown earlier were run in a Python REPL (Read-Eval-Print Loop) or Python Shell environment. If you write the code in a Python file (e.g., `main.py`) and then run it using `python main.py`, you might observe a different outcome: identical integers, regardless of their value (even outside the -5 to 256 range), might share the same memory address.

This is because when you execute `python main.py`, the Python compiler analyzes and optimizes the entire code beforehand. If it detects two integer objects with the same value, it will make them reference the same object to save memory. In the Python REPL environment, however, the compiler processes code line by line. This limits its optimization capabilities, making the Integer Cache mechanism more apparent.

## Conclusion

In this article, we've explored Python's Integer Cache mechanism, focusing on how it applies to integers in the -5 to 256 range. We also delved into CPython's source code to understand the concept of Reference Count for these integer objects. Understanding such details can provide deeper insights into Python's performance characteristics.

## References

- [Python Object Caching - How Does Python Optimize Memory Management for Integers?](https://micahondiwa.hashnode.dev/python-object-caching-how-does-python-optimize-memory-management-for-integers)
- [Python Official Document - Common Object Structures](https://docs.python.org/3/c-api/structures.html#c.PyObject)
- [Python Official Document - Integer Objects](https://docs.python.org/3/c-api/long.html)
- [Python Caches Integers](https://www.codementor.io/@arpitbhayani/python-caches-integers-16jih595jk)
- [Why Python is Slow: Looking Under the Hood](https://jakevdp.github.io/blog/2014/05/09/why-python-is-slow/)
- [Python cached integers](https://thepythoncorner.com/posts/2022-06-18-the-sunday-tip-1-python-cached-integer/)
- [Python WAT!? Integer Cache](https://wsvincent.com/python-wat-integer-cache/)
- [What's with the integer cache maintained by the interpreter?](https://stackoverflow.com/questions/15171695/whats-with-the-integer-cache-maintained-by-the-interpreter)
- [Why python integer caches range \[-5, 256\] don't work in similar way on all platform?](https://stackoverflow.com/questions/63188021/why-python-integer-caches-range-5-256-dont-work-in-similar-way-on-all-platf)
