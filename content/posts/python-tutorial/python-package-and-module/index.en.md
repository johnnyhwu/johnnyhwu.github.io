---
# weight: 1
title: "Organize Your Python Code: An Introduction to Packages"
date: 2022-06-19
lastmod: 2025-11-01
draft: false
description: "Learn the key difference between a Python Module and a Package. This beginner-friendly guide explains how to use packages and the __init__.py file to organize your code effectively, with a simple, step-by-step example."
featuredImage: "featured-image.png"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

## Introduction

In the article "[An In-depth Look at Python Modules](../python-module/)", we introduced the concept of Modules in Python, understanding that a Python Module is essentially a Python file containing reusable code. Building on our understanding of Python Modules, we also explained "[What `if __name__ == '__main__'` Does in Python](../python-main/)". In this article, we will introduce what a Python Package is. If a Python Module is a single Python file, then **a Python Package is simply a folder that contains many Python files**. Let's dive deeper to understand what a Python Package is and how to use it.

## What is a Python Package?

In our computer's photo library, we don't just dump all our pictures into one giant folder. We might organize them into different folders based on date or location. Similarly, when we are working on a large-scale Python project that includes numerous Python files (Modules), we don't place all of them in a single directory. Instead, we organize them into different directories based on their functionality:

{{< image src="project-structure.png" caption="The structure of Python files within a project (source: www.programiz.com)" >}}

The image above shows an example. Under the `Game` Package, there are three sub-packages, each containing several Modules. From this example, we can also see that every Package contains a file named "**\_\_init\_\_.py**". This file can be empty; its presence tells Python to **treat this directory as a Python Package, not just a regular folder**!

## Python Package Example

Next, let's create a Python Package to see it in action.

First, create a new folder in Colab named "project". To make this folder a Python Package, we need to add an `__init__.py` file inside it. Let's also add a `main.py` file. The file structure under "project" should look like this:

{{< image src="demo-1.png" caption="The project directory contains __init__.py and main.py" >}}

Next, let's add another Package called "tools" inside the `project` directory. Similarly, to make the `tools` folder a Python Package, we'll add an `__init__.py` file inside it. We'll also add a `tool.py` file. Now, the file structure under "project" looks like this:

{{< image src="demo-2.png" caption="Adding a tool package under the project package" >}}

In `tool.py`, we'll add a function that sums two numbers and then multiplies the result by a third number:

```python {open=true, lineNos=false, wrap=false, header=true, title="tool.py"}
def sum_mul(a, b, c):
    return (a+b)*c
```

In `main.py`, add the following code to import the `tool` Module from the `tools` Package and use the function defined in it:

```python {open=true, lineNos=false, wrap=false, header=true, title="main.py"}
from tools import tool
print(tool.sum_mul(1, 2, 3))
```

Finally, run the following command in the Colab editor to execute `main.py`:

```bash
!python ./project/main.py
```

The output shows that `main.py` successfully used the function defined in the `tool` Module from the `tools` Package. Of course, for different ways to import Modules from a Package or elements defined within a Module, you can refer to the four methods we introduced in the "[An In-depth Look at Python Modules](../python-module/)" article.

## Conclusion

In this article, we introduced the concept of Python Packages. To put it simply, **if a Python Module is a Python file, then a Python Package is a folder that contains many Python files.**
