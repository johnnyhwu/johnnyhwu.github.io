---
# weight: 1
title: "Why Agents Repeat Themselves: A Mini Example"
date: 2026-10-26
lastmod: 2026-10-26
draft: false
description: "A fixture post: Method A stores an agent's workflow as a graph and uses a validation gate to decide which edits to keep, so it beat plain ReAct in 23 of 24 cells."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Have you ever watched an agent repeat the same useless action again and again?

The verdict first: Method A is positive in 23 of 24 cells.

## The Problem

ReAct figures out every step on its own, so it easily repeats actions that do not work.

{{< image src="figure1.png" alt="Left: a knowledge graph; right: a procedure graph." caption="Figure 1 — Knowledge versus procedure. (Source: original paper, Figure 1.)" >}}

## The Method

The graph has the form \( G = (V, E) \), where \( V \) is the set of nodes.

Think of the gate as a checkpoint: a new version must prove it is no worse than the old one before it passes.

$$
S(G) \ge S(G')
$$

{{< fold title="A loophole in the gate" tone="warning" >}}
The validator does not check tool names; only the prompt constrains them.
{{< /fold >}}
