---
# weight: 1
title: "Computer Architecture Explained: The Bridge Between Software and Hardware"
date: 2023-06-22
lastmod: 2025-10-16
draft: false
description: "Understand the crucial role of Computer Architecture as the bridge between software and hardware. This guide clarifies the key differences between Computer Architecture (ISA) and Computer Organization (Microarchitecture) for students and tech enthusiasts."
featuredImage: "featured-image.png"

tags: ["Computer Architecture"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

This article is a study note for the course [ELE 475 Computer Architecture](https://www.coursera.org/learn/comparch)! Therefore, the illustrations in this article are primarily from the course's lecture slides. This article provides a high-level overview of the role Computer Architecture plays in a computer system, its difference from Computer Organization, and finally, what information is included in a Computer Architecture.

## The Role of Computer Architecture

Computer Architecture is a required course for computer science students, but after a full semester of study, do you really understand the role it plays in the entire computer system?

The diagram below excellently explains the task of Computer Architecture:

{{< image src="def.png" caption="The Role of Computer Architecture" >}}

To connect what we want to achieve in "applications" with the fundamental concepts of "physics" at the lowest level, many layers of technological transformation and abstraction are necessary. Computer Architecture serves as the bridge that connects Application and Technology!

To be more precise:

{{< image src="component.png" caption="Tasks Handled by Computer Architecture" >}}

Computer Architecture is responsible for the "Instruction Set Architecture," "Microarchitecture," and "Register-Transfer Level." Technologies above Computer Architecture tend to be software-oriented, while those below it are more hardware-oriented.

When hardware technology advances (for example, fitting more transistors on a single chip), a better Computer Architecture is needed to unleash the performance gains from these advancements. When the software layer wants to accelerate specific computations (such as speeding up video processing), Computer Architecture needs to design specific instructions to achieve this goal.

Therefore, Computer Architecture, positioned as the central bridge in a computer system, influences both software and hardware development simultaneously, playing a crucial role!

## Computer Architecture vs. Computer Organization

When talking about Computer Architecture, it's often confused with another field: "Computer Organization." Especially in university, these two terms belong to different courses, often leaving students muddled. Here, we'll explain the difference from a relatively simple perspective. Let's start by getting to know their aliases:

*   Computer Architecture = Architecture = Instruction Set Architecture
*   Computer Organization = Organization = Microarchitecture

Hereafter, we'll use Instruction Set Architecture to represent Computer Architecture and Microarchitecture to represent Computer Organization!

Instruction Set Architecture describes the design of a processor from a **Software Engineer's** perspective. For a Software Engineer, the main concern is what kind of Operations, Data Types, and Data Sizes the processor can support.

Therefore, an Instruction Set Architecture defines the many instructions that the processor can support. All these instructions can be broadly categorized into three types:

- Arithmetic/Logic Instructions
- Data Transfer Instructions
- Branch and Jump Instructions

Additionally, it defines the length of these instructions (e.g., 32 bits).

In contrast, Microarchitecture describes the design of a processor from a **Hardware Engineer's** perspective. For a Hardware Engineer, the main concern is how the actual hardware components of the processor should be designed to support the instructions defined in the Instruction Set Architecture.

Therefore, Microarchitecture deals with designing whether the processor can perform Instruction Pipelining, Branch Prediction, or Out-of-Order Execution.

So, the Instruction Set Architecture specifies the operations a processor can support, while the Microarchitecture deals with the implementation details!

In other words, one Instruction Set Architecture can have multiple Microarchitectures. Some Microarchitectures prioritize processor speed, while others focus on cost (the diagram below is an example).

For instance, x86 is an Instruction Set Architecture proposed by Intel. The different generations of processors that Intel releases each year use the same Instruction Set Architecture but have different Microarchitectures, allowing these processors to become faster and faster! A program (referring to its state after being compiled into machine code) that can run on a processor with the x86 Instruction Set Architecture can also run on all other processors with the same ISA!

{{< image src="isa.png" caption="Same ISA but different microarchitecture" >}}

## Basic Information in an Instruction Set Architecture

As mentioned above, the Instruction Set Architecture describes a processor from a Software Engineer's perspective, detailing what instructions the processor supports! The basic information within an Instruction Set Architecture includes:

*   **Instruction Types**: Classifying all instructions into several categories.
*   **Addressing Modes**: The ways in which data can be read from memory.
*   **Data Types and Sizes**: The types and widths of data.
*   **Instruction Encoding**: The width of an instruction and the meaning of each byte.

First, an Instruction Set Architecture categorizes all instructions. As shown below, some instructions are for transferring data (e.g., Load, Store), some are for mathematical operations (e.g., ADD, SUB), and others are for flow control (e.g., Branch If Equal to Zero).

{{< image src="isa-kind.png" caption="Instructions can be divided into multiple types" >}}

Furthermore, it clearly defines the supported Addressing Modes, which are the methods for reading data from memory. Notably, it's not always necessary to read data from memory; for example, the Register Addressing Mode only requires reading data from a register:

{{< image src="isa-type.png" caption="The ISA also clearly defines the Addressing Modes supported by the processor" >}}

Speaking of reading data, the Instruction Set Architecture also clearly defines the Data Types and Sizes supported by the processor:

{{< image src="isa-width.png" caption="The ISA also defines Data Types and Sizes" >}}

Just as data has a size, instructions themselves also have a size! From the diagram below, we can see that ISAs in the Reduced Instruction Set Computer family are typically Fixed Width, meaning every instruction has the same width.

For example, in the MIPS ISA, all instructions are 32 bits. In contrast, ISAs in the Complex Instruction Set Computer family are usually Variable Length, meaning the length of instructions can vary. For example, in the x86 ISA, instruction lengths can range from 1 byte to 17 bytes.

{{< image src="isa-size.png" caption="Instruction sizes differ across various ISAs" >}}

## Conclusion

In this article, we've learned that Computer Architecture plays a crucial "bridge" role in the computer system. We also understood its difference from Computer Organization (Software Engineer's Perspective vs. Hardware Engineer's Perspective). Finally, we explored the kind of information that an Instruction Set Architecture contains.
