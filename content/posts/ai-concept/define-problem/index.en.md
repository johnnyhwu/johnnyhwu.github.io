---
# weight: 1
title: "Machine Learning in 5 Steps: How to Define the Problem"
date: 2023-01-27
lastmod: 2023-01-27
draft: false
description: "Part 1 of a 5-step ML workflow: how to define a problem clearly, and tell supervised learning (regression, classification) apart from unsupervised clustering."
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

In earlier articles, we talked about what machine learning is, and about the relationship between a model, model training, and model inference — and we saw that machine learning can tackle problems that traditional, rule-based programs simply can't. But knowing what machine learning *can* do is still a step away from actually handing a real problem over to it.

This article closes that gap: what five steps you actually walk through when solving a problem with machine learning, and what the first of those steps — "define the problem" — really involves. Whether you're predicting housing prices or classifying images, no matter what model or training method you swap in, these five steps stay roughly the same. Having this flow chart in mind before you start makes it much less likely you'll lose your way once you get into the details.

## The Five Steps of Machine Learning

{{< image src="machine-learning-in-five-steps.jpg" alt="A cyclical diagram illustrating the five steps of solving a problem with machine learning." caption="The five steps of solving a problem with machine learning" >}}

Solving a problem with machine learning usually walks through these five steps:

1. **Define Problem**
2. **Build Dataset**
3. **Train Model**
4. **Evaluate Model**
5. **Use Model**

In practice this isn't a straight line you walk once and finish — it's a loop you go around repeatedly. If a model's evaluation results fall short of expectations, you often have to go back and collect more data, or even go all the way back and redefine the problem. The next few articles will dig into each of these five steps one at a time; today we start with the first.

## Step 1: Define the Problem

{{< image src="define-problem-in-machine-learning.jpg" alt="A diagram highlighting the first step of the machine learning workflow, define the problem." caption="The first step of solving a problem with machine learning: define the problem" >}}

"Define the problem" means exactly what it says: get clear on what problem you're actually trying to solve. This step has two goals you should try to hit.

### Narrow the problem down to something concrete

Suppose we're investing in real estate and want a good return. The question that first comes to mind might be: "How do I make money investing in real estate?"

That question is far too broad. Advertising, renovation, picking the right location, timing the market — every one of those could count as an answer, which leaves you not knowing where to even start. So we need to narrow the question down. Making money on a real estate investment really just means buying a property for less than its actual value, so the question can be narrowed to: "How do I predict the value of a house?"

The more concretely a problem is defined, the clearer it becomes which machine learning algorithm can solve it. That's exactly why "define the problem" deserves to be its own step: skimp on it here, and everything downstream — picking a model, preparing data — ends up fuzzy too.

### Identify which machine learning task the problem belongs to

In the "what is machine learning" article, we mentioned that machine learning algorithms fall into three categories: Supervised Learning, Unsupervised Learning, and Reinforcement Learning. Each learning approach has the kinds of tasks it's good at, so once a problem is defined, the next thing to do is figure out which category of task it belongs to. This article focuses on the tasks that supervised and unsupervised learning are each suited for.

## Supervised vs. Unsupervised

{{< image src="supervised-learning-vs-unsupervised-learning.jpg" alt="A side-by-side comparison diagram contrasting supervised learning and unsupervised learning." caption="The difference between supervised learning and unsupervised learning in machine learning" >}}

The key difference between supervised and unsupervised learning is whether there's a "supervisor" standing next to the computer as it learns. When the computer gets something wrong, the supervisor tells it what the correct answer actually is.

In the language of data, that comes down to whether the data has been prepared with **labels**. A label is simply the correct answer that a given piece of data corresponds to. If every sample has a corresponding label, it's supervised learning; if there are no labels and the model has to find patterns in the data on its own, it's unsupervised learning.

## Tasks in Supervised Learning

Back to the "predict housing prices" example. We want to feed a house's "square footage" into a model and have it output the corresponding "price." The training data would contain a large number of samples, and each sample represents "one house," recording that house's **square footage** and **actual price**.

**Sample: (square footage, actual price)**

During supervised learning's training process, four things happen for every single sample:

- Feed the square footage into the model
- The model outputs a predicted price
- Compare the model's predicted price against the actual price
- Adjust the model's parameters so the output gets closer to the actual price

The actual price in each sample is the label — it represents the correct answer for that sample. And because this label is numeric, this kind of task, where the model predicts a numeric value, is called **"Regression."**

Labels can of course also be "non-numeric" — categorical labels, for instance. Imagine we want to train a model that takes a person's basic information as input and outputs that person's "gender." In that case, each sample represents one person, recording that person's information — say, height, weight, age, and school year.

**Sample: (height, weight, age, school year, gender)**

Here, "gender" is the label for each sample — the correct answer — and it might be "male," "female," or "other." This kind of label is categorical, and the task of having a model predict a category is called **"Classification."**

## Tasks in Unsupervised Learning

Unsupervised learning's data has no labels, so what the model needs to do is different too. Let's use houses again as the example: this time we don't want the model to predict the actual price of each house — instead, we want it to "cluster" a large batch of houses.

Each sample on hand still represents one house, recording a lot of information about it — say, square footage, house age, number of bedrooms, number of bathrooms, current asking price, and so on.

**Sample: (square footage, house age, number of bedrooms, number of bathrooms, current asking price)**

We want the model to cluster these samples — that is, assign each sample to a group. In the process of clustering, the model has to work out the relationships between samples on its own, grouping together samples that are more similar to each other. We never provide any labels at all during this process — how many groups end up forming, and what each group looks like, is something the model learns entirely from the structure of the data itself. That also means the "meaning" of each cluster has to be interpreted by a human afterward — one cluster might, say, turn out to be mostly small, older houses near the city center.

**"Clustering"** is the most basic and most common task in unsupervised learning.

## An Overview of Task Types

{{< image src="task-in-machine-learning.jpg" alt="A diagram classifying machine learning tasks under supervised and unsupervised learning." caption="A simple classification of tasks in machine learning" >}}

Putting the three tasks above side by side makes the distinction clearer:

| Task | Category | Label Type | Model Output | Example |
|---|---|---|---|---|
| Regression | Supervised Learning | Numeric | A number | Predicting housing price from square footage |
| Classification | Supervised Learning | Categorical | A category | Predicting gender from basic information |
| Clustering | Unsupervised Learning | No label | The cluster a sample belongs to | Grouping houses into types |

What defining a problem really boils down to answering is the leftmost column of that table: does the problem in front of you ultimately need the model to output a number, a category, or a clustering result?

## Conclusion

This article introduced the five steps you have to walk through to solve a problem with machine learning, and went deep on the first one, "define the problem": narrowing a problem down to something concrete, then identifying which task category it belongs to in machine learning. We also saw that supervised learning covers "regression" and "classification," while unsupervised learning covers "clustering."

The next article picks up with the second step in the workflow: [building a dataset](../prepare-dataset/).
