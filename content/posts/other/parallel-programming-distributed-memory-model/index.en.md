---
# weight: 1
title: "Distributed Memory Model, MPI, and the Deadlock Trap"
date: 2023-02-24
lastmod: 2023-02-24
draft: false
description: "How the Distributed Memory Model splits a program into independent processes, how MPI handles message passing, and how a naive send/receive order causes deadlock."
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

In the previous article, "Parallel Programming Model: Shared Memory Model," we introduced the first of the [parallel programming](../what-is-parallel-programming/) models, the one that usually produces Multi-Thread programs: multiple threads share the same block of memory and communicate by reading and writing that shared data.

This article covers the second model, the Distributed Memory Model. It takes the exact opposite approach: every execution unit has its own independent memory, none of them can touch each other's data, and the only way to communicate is by explicitly "sending messages." We'll go from the model's basic concept to the Message Passing Interface (MPI), then use a simple two-element summation example to demonstrate the most common pitfall of this model, Deadlock, and finish by comparing the pros and cons of both models side by side.

## What Is the Distributed Memory Model

In the Shared Memory Model, we treat a program as a single process in main memory, and the program's parallelism comes from the multiple threads under that process. The Distributed Memory Model is the opposite: it typically produces a "multi-process" program, where a single program consists of many processes, each independent, each with its own memory, and all running simultaneously on different cores/processors.

{{< image src="distributed-memory-model-architecture.jpg" alt="Architecture diagram of the Distributed Memory Model, showing multiple processes each with its own independent memory, running on different processors." caption="Distributed Memory Model overview" >}}

As shown above, a program contains 3 processes, each running on a different processor. On our computers, the operating system (OS) already treats every process as an independent entity that doesn't interfere with or affect the others, each with its own memory. In other words, Process A has no way to directly access Process B's data — this is protection enforced at the OS level, not a matter of the program not being clever enough.

So here's the question: how do processes within the same program actually communicate with each other?

## Message Passing Interface

In the Distributed Memory Model, different processes communicate through "message passing." Message passing is like sending a letter in real life: one person "sends" a letter, and another "receives" it. It's the same on a computer — one process sends data out, and another process receives it.

There's a key difference from the Shared Memory Model here. Shared memory communication is "implicit" — two threads simply load and store the same block of memory, and nothing in the code visibly shows "who I'm communicating with." Distributed memory communication is "explicit" — the code genuinely contains two actions, Send and Receive, and the direction data flows is written out in plain sight.

In practice, there are many ways to implement message passing, but nobody wants to build one from scratch on top of raw sockets. To ease the developer's burden, communication between processes is usually implemented through a library's Message Passing Interface (MPI).

{{< image src="mpi-send-receive.jpg" alt="MPI communication diagram showing two processes exchanging data through MPI's Send and Receive interfaces." caption="Processes communicate through the Message Passing Interface [source: Parallel Programming Course from NYCU]" >}}

As shown above, with MPI, developers don't need to worry about how data actually gets moved from one process to another under the hood — they only need to clearly specify "which process sends what data" and "which process receives it."

## Distributed Memory Model Example

With the concept covered, let's walk through a very simple example to see what kind of problem actually shows up when writing this model in practice.

{{< image src="example-computation-flow.jpg" alt="Diagram of the example's computation flow: array elements A1 and A2 are each processed by function f and then summed to get S." caption="Distributed Memory Model example" >}}

As shown above, we have an array containing two elements, A1 and A2. The goal is to run function f on each of them and then sum the results to get S.

Suppose the computer happens to have 2 processors. Following the Distributed Memory Model, we can write this as a two-process program: Processor 1 runs Process 1, which handles A1, and Processor 2 runs Process 2, which handles A2. Once each side finishes computing, it sends its half of the result to the other, so both sides end up holding both values and can sum them.

{{< image src="example-pseudocode-send-first.jpg" alt="Pseudocode where two processors each compute a value and then send/receive results from each other, with both sides sending first." caption="Each processor computes its own element and sends the result to the other processor [source: Parallel Programming Course from NYCU]" >}}

The figure above shows this idea written as pseudocode. Each processor computes the element it's responsible for and stores the result in `xlocal`, then sends (`send`) `xlocal` to the other processor, and receives (`receive`) the value the other side sent, storing it in `xremote`.

## Deadlock

The pseudocode above looks harmless, but it actually hides a serious bug that will cause the program to freeze in a Deadlock.

Deadlock is a concept you're bound to run into when studying operating systems. Put simply, a deadlock is a group of processes that are each waiting on a resource the other is holding, so none of them can move.

Here's a real-life analogy: my classmate and I are in art class, each working on our own project. Partway through, I realize I need the scissors he's holding to keep going, and he realizes he needs the glue I'm holding to keep going. If we both insist on holding onto our own resource and just wait for the other to hand theirs over first, we'll both end up stuck exactly where we are.

If you'd like to understand Deadlock in operating systems in more depth, [this article](https://wangwilly.github.io/willywangkaa/2018/07/10/Operating-System-Deadlock/) is a good reference.

{{< image src="example-pseudocode-send-first.jpg" alt="Pseudocode where two processors each compute a value and then send/receive results from each other, with both sides sending first." caption="Each processor computes its own element and sends the result to the other processor [source: Parallel Programming Course from NYCU]" >}}

Back to the pseudocode above. When Processor 1 executes **send xlocal, proc2**, it sends `xlocal` to Processor 2 — and it must wait until Processor 2 actually executes **receive xremote, proc1** and picks up the message before Processor 1 can continue.

The problem is that both sides' first action is a send. If, by unlucky coincidence, both processors execute their send at the same moment (Processor 1 running **send xlocal, proc2**, and Processor 2 running **send xlocal, proc1**), both end up stuck at their send line waiting for the other to receive — and the other is equally stuck at its own send, with neither ever reaching receive. The program just stops there.

{{< image src="example-pseudocode-fixed.jpg" alt="Revised pseudocode where Processor 2 now receives before sending, offsetting it from Processor 1." caption="Avoiding deadlock by ensuring the two processors don't send at the same time [source: Parallel Programming Course from NYCU]" >}}

The fix is actually simple: just make sure the two processors never send at the same time. The figure above swaps the order of Processor 2's send and receive, so Processor 1 sends first while Processor 2 receives first — the two actions are offset, and the deadlock can no longer happen.

## Shared Memory vs. Message Passing

At this point, the communication style of both models should be clear: in the Shared Memory Model, different threads communicate through "shared memory"; in the Distributed Memory Model, different processes communicate through "message passing." So which one is better?

**It depends!** Neither approach is strictly superior — it comes down to the actual problem and the hardware environment. Here's a quick rundown of both models' pros and cons:

- **Shared Memory pros**
  - Implicit Communication: through shared memory, two threads don't need to actually send/receive information — they just load/store it in the shared memory
  - Low Overhead when Cached: on a system with cache, a processor accessing data in cache is far faster than accessing main memory
- **Shared Memory cons**
  - Requires Synchronization Operations: needs substantial synchronization machinery to make sure one thread has already stored the latest data before another thread loads it
  - Hard to Control Data Placement in a Caching System: this is the classic "cache cuts both ways" problem. Cache speeds up data access, but it also introduces False Sharing. False Sharing doesn't produce incorrect results, but it can drag performance down significantly, eating away the benefits parallelism was supposed to bring
- **Message Passing pros**
  - Explicit Communication: communicating explicitly (Send/Receive) makes the direction data flows obvious, which can actually help avoid bugs
  - Easy to Control Data Placement in a Caching System
- **Message Passing cons**
  - High Overhead: sending/receiving data between processes costs more time than shared memory does
  - Complex to Program

## Conclusion

This article introduced the second parallel programming model, the Distributed Memory Model: processes are independent of one another, share no memory, and can only exchange data by explicitly sending/receiving messages — a job usually handed off to a library like MPI. We also walked through a two-element summation example and saw that if the send/receive order isn't offset between the two sides, the program can get stuck in a Deadlock.

Finally, putting the two models side by side, their strengths and weaknesses turn out to be almost complementary: Shared Memory has low communication cost but troublesome synchronization and hard-to-control cache behavior, while Message Passing is more tedious to write and has higher communication cost, but its data flow is clear and easy to control. Which one to actually pick still comes down to the problem in front of you.
