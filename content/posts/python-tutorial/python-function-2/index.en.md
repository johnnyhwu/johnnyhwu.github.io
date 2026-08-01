---
# weight: 1
title: "Understanding Functions in Python (Part 2)"
date: 2026-05-25
lastmod: 2026-05-25
draft: false
description: "Going deeper into Python functions: default and keyword arguments for more flexible calls, plus a thorough look at scope and the lifetime of local and global variables."
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

In [Understanding Functions in Python (Part 1)](../python-function/), we started from the most basic function and worked through functions with parameters and functions with return values, along the way explaining Python's `None` and `NoneType` concepts.

This article carries on to three concepts you'll use every day in practice: default arguments, keyword arguments, and scope. The first two determine "how you can pass arguments when calling a function", while the last determines "how long a variable created inside a function lives, and who can see it".

## Default Arguments in Python Functions

Let's start with a simple example reviewing the previous article:

```python
def say_hello(name):
    print(f'hello, {name}')
```

The code above defines a `say_hello` function that accepts one parameter. When calling it, we pass in a string:

```python
say_hello('Tom')
```

The string "Tom" then corresponds to the `name` parameter.

Now here's the question: what if we call `say_hello` without passing anything?

```python
say_hello()
```

The computer displays an error message:

```text
TypeError: say_hello() missing 1 required positional argument: 'name'
```

The reason is simple: when defining `say_hello` we stated that it accepts one parameter, but nothing was passed in at call time, so the computer doesn't know what value to substitute for `name` and has no choice but to raise an error.

Following that line of thought, if we want calling `say_hello` not to error out even when nothing is passed, we can give the `name` parameter a **default value**:

```python
def say_hello(name="Johnny"):
    print(f'hello, {name}')

say_hello()
```

Now, even if nothing is passed at call time, the computer knows to treat `name` as "Johnny". Of course, if a value is passed in, that value overrides the default.

Put plainly, a "default argument" is simply a parameter that carries a "default value".

## Mixing Parameters With and Without Default Values

When defining a function, if some parameters have default values and some don't, you must make sure that **parameters without default values go on the left**.

For example:

```python
def say_hello(age, name="Johnny"):
    print(f'I am {name}')
    print(f'I am {age} years old')
```

`say_hello` accepts two parameters, `age` (no default value) and `name` (with a default value), so `age` must be written to the left of `name`. If you put them on the wrong side:

```python
def say_hello(name="Johnny", age):
    print(f'I am {name}')
    print(f'I am {age} years old')
```

the program errors out at the moment of definition — it never even gets as far as being called:

```text
SyntaxError: non-default argument follows default argument
```

## Keyword Arguments in Python Functions

When calling a function, the information we pass in is matched to the function's parameters by "position".

Take the `say_hello` function defined above:

```python
def say_hello(age, name="Johnny"):
    print(f'I am {name}')
    print(f'I am {age} years old')
```

Because `name` has a default value, you can pass either one argument or two when calling it. If you pass just one:

```python
say_hello(100)
```

that argument (100) corresponds to `say_hello`'s `age` parameter, while `name` falls back to its default of "Johnny". When we pass two arguments:

```python
say_hello(100, Tom)
```

the **first** argument passed in (100) corresponds to `say_hello`'s **first** parameter, `age`; the **second** argument passed in (Tom) corresponds to the **second** parameter, `name`. Get the order muddled and the values land on the wrong parameters.

Besides matching by "position", we can also use a "keyword" to specify directly which parameter a value goes to:

```python
say_hello(age=100, name="Tom")
```

Once specified by keyword, the order of the arguments can be changed freely — written like this the result is exactly the same:

```python
say_hello(name="Tom", age=100)
```

When there are a lot of parameters, this style is far more readable: the calling line alone tells you what each value is for, without having to go back and look up the function's definition.

## Keyword Arguments of the print( ) Function

Keyword arguments aren't exclusive to functions you write yourself — the `print()` we use every day actually takes several parameters. For example, after `print()` displays a string it appends a "newline character" at the end by default, which is why whatever the next `print()` outputs ends up on the next line:

```python
print('Hello')
print('Johnny')
```

After running this, Hello is on the first line and Johnny on the second:

```text
Hello
Johnny
```

If we want Johnny not to go on a new line but to follow directly after Hello, we can use the `end` keyword argument to specify the characters appended to the end of the string.

For example, appending nothing at all to the end of the Hello string:

```python
print('Hello', end="")
print('Johnny')
```

The displayed result is now:

```text
HelloJohnny
```

Or appending "a single space" to the end of the Hello string:

```python
print('Hello', end=" ")
print('Johnny')
```

The displayed result is now:

```text
Hello Johnny
```

In other words, the line break you normally see is just `end`'s default value happening to be a newline character — it isn't behaviour hard-coded into `print()`.

## The Concept of Scope in Python

In [the previous article](../python-function/) we mentioned that accessing a variable from "inside" a function while "outside" that function makes the computer raise an error. For example:

```python
def say_hello(age, name="Johnny"):
    print(f'I am {name}')
    print(f'I am {age} years old')

print(age)
```

```text
NameError: name 'age' is not defined
```

Because the variable `age` exists only inside the `say_hello` function, it cannot be accessed outside it. A function has its own "range", its own "boundary" — and that is the concept of **scope** in programming languages.

## Local Scope and Global Scope

Scope divides into local scope and global scope: the inside of a function forms a local scope, while everything outside functions belongs to the global scope. A variable created in a local scope is called a **local variable**; a variable created in the global scope is called a **global variable**. A variable can only have one identity — it is either a local variable or a global variable, never both.

```python
a = 5
b = 10

def example():
    c = 15
    d = 20

e = 25
```

Taking the code above as an example, the variables a, b and e are all in the global scope and are global variables; the variables c and d are written inside a function, are in a local scope, and are local variables.

Clever reader that you are, you've surely noticed: variables inside a function are local variables, and variables outside functions are global variables. A program can have many local scopes (potentially as many as it has functions), but it will only ever have one global scope.

## The Lifetime of Variables in Python

Now that we know variables divide into local and global, the next thing to look at is how long each of these two kinds "lives".

When a **"function"** runs, the local scope belonging to that function is created too, and the variables created in the function are all stored in that local scope. When the function finishes running, that local scope is destroyed along with it, and the local variables stored inside it naturally disappear too. This also explains why `print(age)` earlier came up empty: once the function has run, `age` no longer exists.

When a complete **"program"** (.ipynb or .py) starts running, the global scope belonging to that program is created too, and the variables created in the program are all stored in that global scope. When the program finishes running, that global scope is destroyed along with it, and the global variables stored inside it disappear too.

## Important Properties of Scope in Python

Having understood local scope and global scope, we can lay out four important properties of scope:

- Code in the global scope may not access variables in a local scope (local variables)
- Code in a local scope may access variables in the global scope (global variables)
- Code in a local scope may not access variables in another local scope (local variables)
- If two variables are in different scopes, those two variables may use the same name

## Conclusion

This article introduced default arguments and keyword arguments in Python functions, which give us more flexibility when defining and calling functions. It also explained the concept of scope, along with the respective lifetimes of local variables and global variables.

The four properties of scope listed at the end are the key to understanding "why a variable is sometimes readable and sometimes not". The [next article (Understanding Functions in Python Part 3)](../python-function-3/) explains what each of these four properties means, one at a time.
