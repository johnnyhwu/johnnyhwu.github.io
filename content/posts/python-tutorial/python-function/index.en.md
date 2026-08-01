---
# weight: 1
title: "Understanding Functions in Python (Part 1)"
date: 2026-05-13
lastmod: 2026-05-13
draft: false
description: "Understand Python functions from scratch: defining them with def, parameters vs arguments, returning values, and the NoneType and None gotcha."
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

In previous Python tutorial articles we have already used the word "function", and we've called several of Python's built-in functions such as `print()`, `len()` and `input()`. Up to now, however, we have only been "using functions other people wrote".

This article flips that around: what a function actually is, why functions exist, and how to define your own. We'll start with the most basic way to write a function, then cover functions with parameters, functions with return values, and finally a concept that frequently trips up beginners — NoneType and None.

Put plainly, a function packages up a piece of code that "gets reused, or has a clear job" into a single bundle and gives it a name. When you want it later you just call that name, instead of copying the same code out again.

## Functions in Python

Let's start with this piece of code:

```python
def first_function():
    print('Hello World')

first_function()
```

This code does two things: it defines a function named `first_function`, and then calls it. Let's break down its component parts.

On line 1, `def` is a keyword indicating that we are "defining" a function. The `first_function` following `def` is the function's "name", which is what we'll use to call it later. After the name we also add a pair of "parentheses", whose purpose will be explained shortly.

After writing `def`, the function name and the parentheses, we still need to specify what code runs inside the function. The syntax here is the same as for [for loops and while loops](../python-loop/): add a "colon" at the end of the line, and the code inside the function must be "indented". Those indented lines are the function's body, and they only run when the function is called. In the example above, the function body is just the single line `print('Hello World')`.

The last line of the code block, `first_function()`, is "calling" this function. Calling is simple: write the "function name" followed by "parentheses".

So what are the parentheses actually for? You can supply arguments to the function inside them. For example, when we use the built-in `print()` function, we put the string we want displayed inside the parentheses:

```python
print('Hello World')
```

As for execution order, you can think of it this way: when the computer reaches the line that "calls a function", it first jumps to the first line inside that function and starts running; once all the code in the function has finished, it jumps back to where the call was made and carries on with the code that follows.

For example:

```python
def first_function():
    print('Hello World')

first_function() #1
print('執行完 1 次') #2
first_function() #3
print('執行完 2 次') #4
```

After the first call to `first_function` (#1), the computer jumps into `first_function` and runs `print('Hello World')`. Once all the code inside the function has run, it returns to position #1 and continues on to #2, #3 and #4. So the final output is:

```
Hello World
執行完 1 次
Hello World
執行完 2 次
```

Notice that `Hello World` appears twice even though we only wrote `print('Hello World')` once. This is the most immediate benefit of functions: write the same logic once, then call it as many times as you need.

## Functions with Parameters in Python

By now you should be quite comfortable using `print()` to display the string you want. That string we put inside the parentheses is called an **argument**, and it gets passed into the function at the moment the function is called.

Functions you define yourself can of course accept arguments too:

```python
def second_function(name):
    print(f'Hello, {name}')

second_function('Johnny')
```

Inside the parentheses after the function name `second_function`, we placed a variable `name`. This variable is called a **parameter**, and it specifies what this function is able to accept. So when I pass in the string `'Johnny'` at call time, the displayed result is:

```
Hello, Johnny
```

At this point parameters and arguments may have your head spinning. There's really no need to agonise over the two terms — just remember which stage each one belongs to:

- **Parameter**: at the "defining the function" stage, specifying what this function is able to accept. For example `name` in the code above.
- **Argument**: at the "calling the function" stage, what actually gets passed into the function. For example `'Johnny'` in the code above.

One thing deserves particular attention: the parameters a function accepts can be used as ordinary variables inside the function, but once the function finishes running those variables are destroyed, so you cannot get at them outside the function.

For example, let's add a line `print(name)` below `second_function('Johnny')`:

```python
def second_function(name):
    print(f'Hello, {name}')

second_function('Johnny')
print(name)
```

The result of running this is:

```
NameError: name 'name' is not defined
```

The reason is that the variable `name` was destroyed once `second_function` finished running, so it cannot be used outside the function.

## Functions with Return Values in Python

Besides `print()`, we also frequently use the `len()` function to get a string's length:

```python
name = 'Johnny'
length = len(name)
print(length)
```

This code displays the length of the string `name`. The key point here is that after `len()` is called it "returns" an integer, which is what lets us store it in the `length` variable. This is unlike `print()` — `print()` merely displays something on screen and doesn't hand back any result you can go on to use.

If you want a function you've written to return a value to the place it was called from once it finishes, you have to use the `return` keyword:

```python
def third_function(name):
    return f'Hello, {name}'

output = third_function('Johnny')
print(output)
```

In `third_function`, we return a string with `return`. So the result of running `third_function('Johnny')` is `Hello, Johnny`, which is stored in the `output` variable.

Something else to note: when a function reaches `return`, that function is finished, and code after the `return` will not run:

```python
def fourth_function(name):
    return f'Hello, {name}'
    print('under return keyword')

output = fourth_function('Johnny')
print(output)
```

The result of running this code is exactly the same as the previous snippet, because in `fourth_function` the line `print('under return keyword')` sits after the `return` and is therefore never reached.

## NoneType and None in Python

In the earlier article introducing Python variables and data types, we covered Python's basic data types such as integer, string and floating-point number.

Today we'll introduce one more data type, called **NoneType**. NoneType is unusual in that it has exactly one value: `None`. A type containing only 1 or 2 values isn't actually strange — the boolean type we learned about earlier contains only the two values `True` and `False`.

So why learn about this somewhat magical-looking NoneType? The reason has to do with function return values.

In Python, every function has a return value — that is, every function call is guaranteed to produce a value. Calling `third_function()`, `fourth_function()` and `len()` all give you a value, which feels intuitive. The problem is that for a function to have a return value you must write `return ...`, and we don't always write that line — `first_function()` at the very start of this article, for instance, doesn't.

Python's approach is this: as long as a function we define has no `return ...`, Python automatically adds a `return None` for us. Let's look back at `first_function()`:

```python
def first_function():
    print('Hello World')

output = first_function()

if(output == None):
    print(f"output is None")
```

We store the result of running `first_function()` in the `output` variable, then check whether `output` equals `None`. The final output is:

```
Hello World
output is None
```

This confirms it: even though `first_function()` returns no value — that is, has no `return ...` written in it — Python still automatically adds a `return None`, making the function's final return value `None`. This is also why storing the result of `print()` in a variable and printing it shows you `None` rather than the text that was just displayed.

## Conclusion

This article started from the most basic function definition and worked through functions with parameters, functions with return values, and the concepts of NoneType and None in Python. With these points under your belt, you can already package repeated code into functions to make your code more readable and easier to maintain.

But one question remains unanswered: within what scope do the variables inside a function actually "live"? The [next article (Part 2)](../python-function-2/) covers a deeper concept about functions: function scope.
