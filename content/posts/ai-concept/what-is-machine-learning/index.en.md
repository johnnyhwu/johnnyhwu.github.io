---
# weight: 1
title: "What Is Machine Learning? The Three Families of Algorithms"
date: 2022-01-17
lastmod: 2026-08-31
draft: false
description: "Machine learning builds AI without hard-coding rules: the computer finds patterns in data. A tour of supervised, unsupervised and reinforcement learning."
featuredImage: "featured-image.jpg"

tags: ["Machine Learning"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## Introduction

Machine learning is a software technique, and one of the ways we build artificial intelligence (AI). With AI techniques we don't hard-code a program that teaches the computer how to solve a problem; instead we hand it a large amount of data and let it work out its own way to solve the problem. This article covers what machine learning is, which categories of algorithms it contains, and how machine learning differs from traditional programming.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **What machine learning is**: a family of algorithms that let a computer learn from data, discover the patterns inside it, and make predictions — one concrete way of realising artificial intelligence.
- **Three categories**: supervised learning (with labels), unsupervised learning (without labels), and reinforcement learning (driven by rewards).
- **How it differs from traditional programming**: traditionally a human analyses the data, invents a solution, and writes it down as code; machine learning instead trains a *model* from "lots of data + a training method".
- **Why we need it**: problems like "is this photo a cat or a dog?" have far too many features to ever enumerate by hand.
{{< /admonition >}}

## What is machine learning

{{< image src="AI-vs-ML-vs-DL.jpg" alt="A diagram of the relationship between AI, ML and DL, showing the three as nested from outermost to innermost." caption="The relationship between AI, ML and DL [source: Nvidia]" >}}

Machine learning is a family of algorithms that lets a computer learn from data, discover the rules and patterns within that data, and make predictions from them. It is also one way of realising *artificial intelligence*. And what is artificial intelligence? It refers to a computer being able to solve problems as though it possessed human-like intelligence.

There are a great many algorithms under the machine learning umbrella that help a machine (a computer) learn from data. Deep learning, shown in the diagram above, is one particular kind of them. Deep learning of course contains many algorithms of its own, but those are beyond what this article sets out to teach.

## What algorithms does machine learning contain

{{< image src="algorithm-in-ML.jpg" alt="A diagram showing machine learning algorithms divided into three major categories." caption="The algorithms under machine learning fall mainly into three categories" >}}

As mentioned above, machine learning contains a great many algorithms, but broadly speaking they can be separated into three categories: **supervised learning**, **unsupervised learning**, and **reinforcement learning**. Each category contains many algorithms of its own, and each has its own distinct character.

### Supervised learning

The first is supervised learning. Why "supervised"? Because this style of learning is like having a supervisor standing next to the computer watching it learn. You typically prepare a great deal of *data* along with the *labels* for that data. After looking at a piece of data, the computer has to say what its label is. Even when the computer gets it wrong, the correct label was prepared in advance, so the computer can find out what the right answer was.

It is like a child learning the letters of the English alphabet with a teacher listening beside them: if the child mispronounces a letter, the teacher immediately corrects them and tells them the right pronunciation.

### Unsupervised learning

The second is unsupervised learning. Unlike supervised learning, there is no supervisor standing next to the computer telling it the right answer. The computer has to feel its way forward and find the underlying regularity on its own. In other words, we prepare a lot of *data* for the computer but no labels for it. The computer has to observe the data itself, work out where the items are alike and where they differ, and discover the pattern they follow.

It is like a baby sorting mung beans from red beans. The baby has no idea which is which; it simply puts "the green ones" on one side and "the red ones" on the other based on observation.

Which task types each of these two styles suits — regression, classification, clustering — is discussed more fully in [defining the problem](../define-problem/).

### Reinforcement learning

The third is reinforcement learning. Compared with the previous two, this style of learning is much more *human*, and involves two important elements: an *agent* and an *environment*. The agent observes its surrounding environment and takes an *action*. The environment then hands that action a *reward* according to how good or bad it was. The agent's ultimate goal is to collect as much reward as possible, and to reach that goal it learns to perform better.

In practice we know this style of learning all too well. At school and at work we are praised for doing things right and reprimanded for doing things wrong, and through that we come to judge situations better and understand how to do a job well.

## Machine learning vs. traditional programming

{{< image src="machine-learning-vs-traditional-programming.jpg" alt="A side-by-side diagram contrasting how machine learning and traditional programming each go about solving a problem." caption="The difference between machine learning and traditional programming [source: Udacity]" >}}

In traditional software development it is usually a *human* who analyses the data. Through the data we come to understand what the problem is, then dream up a solution, and finally turn that solution into a program by writing code.

For example: I often forget to check the weather forecast, so on rainy days I regularly forget my umbrella and end up soaked. Given that problem, one possible solution is a program that automatically fetches tomorrow's forecast, and if the forecast says rain, sends a LINE notification to my phone. Once you have that line of attack, you can write the program with a web scraper, the LINE Bot API and so on, and the problem is solved.

Some problems, however, cannot be solved by any such clearly-stated method.

For example: recognising whether a photo contains a cat or a dog. Cats and dogs differ in many features of body shape, and dogs alone (or cats alone) come in many breeds, each of which needs many features to tell apart. On top of that, the lighting and viewing angle when the photo was taken also change how the subject looks. Writing every one of those features into a program would take more than a lifetime.

The strength of machine learning is precisely that it can solve this kind of problem. In a machine learning algorithm we usually prepare three elements:

1. A large amount of data
2. A model
3. A method for training the model

Using the "large amount of data" and the "method for training the model", we train a *model* that can recognise whether a picture is a cat or a dog. That is, we feed the picture into the model and the model outputs a result: the probability it is a cat and the probability it is a dog. Machine learning thus solves a problem traditional programming cannot.

## Conclusion

In this article we gained a first understanding of machine learning, learned the three categories of algorithms it contains, and distinguished machine learning from traditional programming. This article is the first in the AWS ML Foundation series; [the next article](../model-training/) will introduce the *model* in machine learning and the *method used to train it*.
