---
# weight: 1
title: "Arithmetic in Python: Understanding Expressions"
date: 2022-01-25T21:21:45
lastmod: 2026-08-06
draft: false
description: "Your first hands-on Python code: arithmetic, how an expression is built from values and operators, the **, % and // operators, and what a SyntaxError really means."
featuredImage: "featured-image.jpg"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

## Introduction

This is the second article in the Python programming beginner's series. In the previous one we got the environment ready; in this one we actually start writing Python code, beginning with the arithmetic everyone already knows — turning maths into something a computer understands.

Besides the four basic operations, this article also introduces the idea of an *expression*. It sounds academic, but it's just the "sum" you've been writing since primary school, restated in programming terms. Once it clicks, variables and conditionals later on go down much more smoothly.

## Opening and Naming a Colab

In the [previous article](../google-colaboratory/) we introduced Google Colaboratory (Colab), a handy online editor. It runs in the browser, so there's no need to install Python on your own machine — the lowest-friction starting point there is for a beginner.

Before writing any Python code, create a new Colab file in your Drive and give it a recognisable name. Every piece of code from here on gets written and run inside a Colab cell.

## Basic Arithmetic

Let's start with the simplest possible program: what is 123 + 456? A calculator answers that in a second, and in Python the code looks almost exactly like the maths:

```python
123 + 456
```

Run that line in a Colab cell and you see the answer straight away. By the same token, if we want to work out 907 - 456, you can certainly write the program immediately:

```python
907 - 456
```

For multiplication and division, note that the symbols differ from your maths textbook: multiplication uses an asterisk `*` and division a forward slash `/`, not `x` and `÷`. Here we compute 1445 x 404 and 1309 ÷ 56:

```python
1445 * 404
1309 / 56
```

If you can write all of the above, you've already learned how to do arithmetic in Python.

## Understanding Expressions

Now let's look at the concept of an expression. In fact, those lines of code we just wrote *are* expressions.

{{< image src="expression.jpg" alt="A diagram breaking an expression into its parts, labelling the values and the operators within the sum." caption="The concept of an expression" >}}

As the figure shows, an expression is made up of two kinds of thing: values and operators. Put more plainly, an expression is a mathematical "sum", containing a number of "values" and "operator symbols".

What characterises an expression is that it can be *evaluated* — a long "sum" can be reduced to a single "value". For instance, 2 + 2 + 2 + 2 + 2 + 2 is an expression that evaluates to 12. So what the earlier code is doing is writing down one line of expression and handing it to the computer to evaluate:

```python
123 + 456
```

One thing to watch: while evaluating, the computer follows the rules "multiplication and division before addition and subtraction" and "whatever is inside the parentheses first". That means `1 + 2 * 3` gives 7, not 9; if you really want the addition first, you have to add the parentheses yourself and write `(1 + 2) * 3`. Keep operator precedence in mind when writing expressions, or you'll get an answer you didn't expect.

## More Advanced Operators: `**`, `%` and `//`

Beyond the basic four operations, Python has three somewhat more advanced operators. First is `**`, meaning "to the power of". For example, run the following code to compute "2 to the power of 3":

```python
2 ** 3
```

`%` means "remainder". For example, 15 ÷ 4 = 3 (quotient 3) ⋯ 3 (remainder 3). If we want the remainder of 15 divided by 4 in a program, we use `%`:

```python
15 % 4
```

Finally, `//` means "quotient". Taking 15 ÷ 4 again, if we want the quotient of 15 divided by 4 in a program, we use `//`:

```python
15 // 4
```

Here's a point that's easy to mix up: `/` produces the ordinary division result, while `//` keeps only the integer part. The two look one slash apart, but their purposes are entirely different.

## Syntax Errors

{{< image src="syntax-error.jpg" alt="A Colab screenshot showing a SyntaxError message raised after running an invalid line of code." caption="A common beginner mistake: SyntaxError" >}}

"Syntax Error" is an error message you'll see often while programming. It means exactly what it says — the computer is telling us there's something wrong with the syntax of the code you wrote. In the figure above, we originally meant to compute:

```python
1 + 3 * 4
```

but the 3 got left out, making it:

```python
1 + * 4
```

A multiplication sign immediately following a plus sign can't be evaluated, of course, so the computer displayed a SyntaxError. Don't panic when you see this message — it usually means a character was missed or typed twice somewhere, and re-reading that line will find it.

One more note: while writing code, we often put "spaces" between numbers and symbols. Those spaces don't cause a syntax error; they're purely there to make the code look tidier and cleaner.

## Conclusion

In this article we learned Python's most basic syntax and the concept of an expression, and implemented a variety of mathematical operations in Python code — the four basic operations plus the three more advanced operators `**`, `%` and `//`. Along the way we also got to know what the SyntaxError that beginners hit most often actually is.

In the [next article](../python-variable-data-type/) we'll introduce the concept of a "variable" in programming, so we can store a computed result and reuse it instead of rewriting the sum every time.
