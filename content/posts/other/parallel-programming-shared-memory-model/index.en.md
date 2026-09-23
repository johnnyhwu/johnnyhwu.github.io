---
# weight: 1
title: "Shared Memory Model, Multi-Threading, and the Race Condition Trap"
date: 2023-02-20
lastmod: 2023-02-20
draft: false
description: "The first parallel programming model: threads share memory implicitly, which leads straight into Race Conditions -- and how Lock-based Critical Sections fix it."
featuredImage: "featured-image.jpg"

tags: ["Parallel Programming"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

Once you know [what parallel programming is](../what-is-parallel-programming/) and why it's needed, the next question is how to actually write it. There are three common parallel programming models, each with its own implementation style and best-fit scenarios. This article covers the first one: the Shared Memory Model.

We'll start from the Shared Memory Model's memory layout, then use a small "sum up the elements of an array" example to surface the trap this model is easiest to fall into — the Race Condition — and finish with how Locks and Critical Sections shut it down.

## What Is the Shared Memory Model

If you've ever used multi-threading in your own code, the idea of shared memory won't be new to you. Programs built with the Shared Memory Model are, generally speaking, what people call "multi-thread programs."

The basic idea is simple: split a program's similar tasks across different threads, and those threads can run on different cores at the same time, shortening the program's overall execution time. Work that would take 8 seconds on its own could, ideally, finish in about 4 seconds split across 2 threads.

If you're still fuzzy on the difference between a thread and a process, [this explainer](https://totoroliu.medium.com/program-process-thread-%E5%B7%AE%E7%95%B0-4a360c7345e5) is a good place to start. For now, think of a program as simply one process living in main memory. In a multi-thread program, that process contains many threads, each with its own private memory (e.g. local stack variables), while all the threads share a block of shared memory (e.g. static variables and the global heap).

{{< image src="shared-memory-architecture.jpg" alt="A memory architecture diagram for the Shared Memory Model, showing several processors each connected to their own memory while all sharing one block of shared memory." caption="Under the Shared Memory Model, every processor has its own memory as well as a block of memory shared with the others" >}}

As shown above, suppose each processor is running a different thread — each thread has its own private memory holding information only it needs, while also sharing a block of memory the threads can use to exchange information.

Here's the key idea: in the Shared Memory Model, threads communicate "implicitly." Nothing in the code tells one thread to explicitly send or receive data from another — each thread just reads from and writes to shared memory, and that's how information gets passed along. Put another way, the shared memory itself *is* the communication channel.

## A Shared Memory Model Example

Let's make the idea above — and the trouble it can cause — concrete with a simple problem and some code.

{{< image src="array-example.jpg" alt="A one-dimensional array diagram containing 8 elements." caption="Suppose we have an array with 8 elements" >}}

As shown above, suppose we have an array with 8 elements. Every element needs to be run through function f, and then all the results need to be summed up.

{{< image src="thread-split.jpg" alt="A diagram showing an array split in half, with the first 4 elements assigned to Thread 1 and the last 4 elements assigned to Thread 2." caption="The first 4 elements go to Thread 1; the last 4 elements go to Thread 2" >}}

To cut down the program's run time, we create 2 threads, each responsible for 4 elements. Thread 1 and Thread 2 each have their own (private) local variable to track the partial sum of the 4 elements they compute; there's also one (shared) static variable that tracks the overall total.

{{< image src="fork-sum-code.jpg" alt="A multi-thread summation code snippet, with a blue box highlighting the fork call that creates a new thread, and the sum function both threads execute." caption="Example code [source: Parallel Programming Course from NYCU]" >}}

Writing the above description out as code looks roughly like the snippet above. Look at the boxed-in part first: a `fork` call creates a new thread (Thread 1), specifies the function it should run (`sum`), and passes in the array elements that thread is responsible for (`a[0 : n/2 - 1]`). The next line has the original main thread run the `sum` function itself, handling the second half of the array (`a[n/2 : n-1]`).

That gives us Thread 1 and Thread 2, both running the same `sum` function. The body of `sum` is mainly a for-loop: each element gets run through function `f`, and the result gets accumulated into the static variable `s` (a variable both Thread 1 and Thread 2 can read and write).

## Race Condition

Looks fine — but if you actually run this code, you'll find the result isn't always correct, and it can even come out different every single time you run it.

The reason is that Thread 1 and Thread 2 run on different cores at the same time. If Thread 1 is reading `s` at the exact moment Thread 2 writes to it, the final result ends up wrong. This kind of error, caused by multiple cores' reads and writes to the same block of memory interleaving in time, is called a **Race Condition**.

Here's a concrete example. Say `s = 16` right now:

1. Thread 1 reads `s = 16`, and is about to add the result of `f(A[i])` to 16 and write it back to `s`.
2. Just before Thread 1 writes back, Thread 2 has already written its own new result into `s`, so now `s = 20`.
3. Thread 1 has no idea any of this happened — it's still holding onto 16, so it computes with 16 and overwrites `s`.

Thread 2's write effectively evaporates, and everything computed after that is naturally wrong. The tricky part is that this kind of bug depends entirely on the two threads' execution timing, so it's intermittent — it might pass 9 times out of 10 in testing, only to blow up occasionally once it's in production.

## Critical Section

To fix the Race Condition in a multi-thread program, we can use a lock mechanism to set up a Critical Section.

{{< image src="critical-section.jpg" alt="An improved code snippet where each thread first accumulates into its own local_s1 or local_s2, and only the final write-back to the shared variable s is wrapped in a lock, with a red-text question shown alongside." caption="Setting up a Critical Section to avoid Race Conditions [source: Parallel Programming Course from NYCU]" >}}

As shown in the code above, the first step is to reduce the odds of a Race Condition happening: give each thread its own local variable (e.g. `local_s1` and `local_s2`) to hold its own partial sum, and only add that partial sum into `s` and write it back at the very end. That way, instead of touching the shared variable on every single iteration of the loop, each thread now only touches it once, total.

But lower odds isn't the same as zero odds. "Add my own total to `s` and write it back" is itself still an action that can collide with another thread doing the same thing.

So the second step wraps that action in a lock, turning it into a Critical Section — the only way to eliminate the Race Condition completely. Once a piece of code becomes a Critical Section, only one thread is ever allowed to execute it at a time; every other thread has to wait for the previous one to leave before it can enter, so interleaved reads and writes simply can't happen anymore.

There's also a line of red text in the figure above: "Why not do lock inside the loop?" In other words: why not go back to the most original version (the one without `local_s1` and `local_s2`) and just wrap a lock around the `s = s + f(A[i])` line inside the for-loop instead? That would avoid the Race Condition too.

The answer is cost. A lock is implemented through a system call, and a system call is an expensive instruction. Put it inside the loop, and you're paying that cost once per element; with enough calls, that extra overhead can end up canceling out most of what multi-threading was supposed to buy you. Moving the lock outside the loop, and only locking the one line that actually needs protecting, is the far better trade.

## Conclusion

This article introduced the first of the parallel programming models — the Shared Memory Model: threads communicate implicitly through memory they share, which is intuitive to write but also an easy way to run straight into a Race Condition.

The basic fix is to fence off a Critical Section with a lock, guaranteeing only one thread can touch the shared data at a time. And it's worth remembering that a lock isn't free — where you place its granularity is often what decides whether parallelizing actually paid off at all.
