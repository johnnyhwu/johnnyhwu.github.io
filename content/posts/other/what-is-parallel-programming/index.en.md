---
# weight: 1
title: "What Is Parallel Programming? A Beginner's Guide"
date: 2023-02-10
lastmod: 2023-02-10
draft: false
description: "Learn what parallel programming is, how it differs from traditional single-threaded (serial) code, and why today's multi-core hardware makes it essential for engineers."
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

This article explains what "parallel programming" is, how it differs from the (non-parallel) programming style we're all used to, and why today's software engineers need it. We'll start from the most basic single-threaded program, so no prior background in parallel computing is required.

## Single-Threaded Programming

To understand parallel programming, it helps to first look back at how ordinary (non-parallel) programs run.

Most of us learn to write code from a "single-thread" perspective: we expect the processor to execute what we write "top to bottom," "line by line." That's the idea behind **serial computing**.

More concretely: back in the era when computers still had a single core, software engineers would break a "problem" down into a series of "instructions," expecting the processor to execute them one by one.

{{< image src="serial-program.jpg" alt="A program broken down into a sequence of ordered instructions, all executed one after another by a single processor." caption="A program is broken down into a sequence of instructions executed by a processor" >}}

Here's the problem: almost any computer today has 4, 8, or more cores. But as long as we keep writing code from a "single-thread" perspective, only one core is ever doing work "at any given moment" — the computing resources of every other core just sit idle, wasted.

## Parallelized Programming

Parallel programming means adding special techniques at the coding stage so that a program can be executed by multiple cores "at the same time." When doing parallel programming, software engineers typically split a problem into "multiple groups" of instructions and hand each group off to a different core to run.

{{< image src="parallel-programming.jpg" alt="A program split into multiple groups of instructions, each handed off to a different processor to execute at the same time." caption="Parallel programming means a single program is executed by multiple processors at the same time" >}}

There's a very practical precondition here: before you can hand different groups of instructions to different cores, you first need to make sure those groups have no "dependencies" between them. In other words, you can't have a situation where one group must finish before another can start. For example, splitting a 1-million-element array into 4 chunks and summing each chunk independently parallelizes nicely, since the chunks don't affect each other; but computing a Fibonacci sequence, where each term depends on the one before it, gains nothing from extra cores.

## What "At the Same Time" Actually Means

We just said parallel programming lets a program run across many cores "at the same time." But in computer science, "at the same time" actually splits into several distinct ideas worth telling apart.

- **Concurrent Computing**

A program is split into many small tasks, and each task is "in progress" — but they aren't truly executing "simultaneously." Instead, they run by "interleaving": for example, Task A and Task B are both in progress, but the core actually finishes a portion of Task A, then switches over to Task B, and so on.

- **Parallel Computing**

A program is split into many small tasks, and each task is "in progress" — and this time, these tasks really are, in theory, executing "at the same time." That's the key difference from concurrency: the former is fast switching, the latter is genuinely running together.

- **Distributed Computing**

Both of the above happen on "a single computer." Distributed computing, in contrast, is distributed computation across "multiple computers." In parallel computing, a single computer typically has multiple processors that share memory to communicate; in distributed computing, there are multiple computers (each one can be thought of as a node), each with its own processor and memory, communicating with one another over a network.

{{< image src="parallel-vs-distributed-computing.jpg" alt="Side-by-side diagram contrasting a single computer with multiple processors sharing memory on the left, against multiple computers each with their own processor and memory connected over a network on the right." caption="The difference between parallel computing and distributed computing" >}}

That shared-memory-versus-per-node-memory split is exactly the kind of memory-model question that comes up once you start actually building parallel programs — see [Parallel Programming: The Distributed Memory Model](../parallel-programming-distributed-memory-model/) for a closer look at how the distributed side of that picture works.

## Why We Need Parallel Programming

Now that we have a sense of what parallel programming is, let's talk about why we need it.

- **Shorter execution time**

The most intuitive reason is that it can shorten a program's execution time. Splitting the original problem into many tasks and processing them with concurrent or parallel computing is, in theory, faster than serial computing (how much faster depends on the nature of the problem itself). For a commercial service, a shorter execution time can also translate directly into revenue.

- **Application requirements**

In the age of big data, the volume of data generated every day has long outpaced what accumulated over the past several decades combined. Some applications need to load so much data that it simply doesn't fit into a single computer's memory. Distributed computing lets that data be spread across multiple nodes instead.

- **Changes in hardware architecture**

Older computers mostly had a single core (single-core), and the way to boost performance was to push the core's clock rate higher. But due to physical limits (heat and power consumption), a single core's clock rate can no longer be pushed much further, so the industry shifted toward multi-core designs. Most computers today ship with 4, 8, or more cores — if a program is still designed in a non-parallel, single-threaded way, that's equivalent to leaving most of the hardware's resources sitting idle. Getting every core to deliver its full performance is a step that parallel programming can't be skipped.

## Conclusion

This article introduced the basic concept of parallel programming, how it differs from single-threaded programming, and clarified the three distinct meanings of "at the same time" — concurrent, parallel, and distributed computing — before covering why parallel programming matters. In the next article, we'll walk through a simple example that shows how parallel programming actually works in practice.
