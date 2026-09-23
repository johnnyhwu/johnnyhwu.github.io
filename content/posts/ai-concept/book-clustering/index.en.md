---
# weight: 1
title: "Solving a Problem with Machine Learning: Exploring Book Styles"
date: 2022-02-05
lastmod: 2022-02-05
draft: false
description: "A worked example in the five-step ML series: clustering books by style with no labels, using K-Means and the silhouette coefficient to pick the right number of clusters."
featuredImage: "featured-image.jpg"

tags: []
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## Introduction

This is the 9th article in the "Machine Learning Fundamentals" series. In the previous post, we used the five-step machine-learning workflow ([Define the Problem](../define-problem/), [Prepare Dataset](../prepare-dataset/), [Model Training](../model-training/), [Model Evaluate](../model-evaluate/), and [Model Inference](../model-inference/)) to work through the "house price prediction" example, and house price prediction is a classic case of Supervised Learning: every piece of data comes with a correct answer, and the model just learns from those answers.

This time we're switching to a different setting. It's the same five steps, but this time there's no ground truth to learn from at all — the problem is "exploring book styles": we feed a batch of book summaries into a model and let it figure out on its own which books share a similar tone. This falls under Clustering, a task within Unsupervised Learning, and it's a very common kind of problem in practice: you know there's structure in the data, but you can't say up front what that structure looks like.

## Step 1: Define the Problem

{{< image src="define-problem-1.jpg" alt="A diagram highlighting the first step of the five-step machine learning workflow, define the problem." caption="Defining what kind of problem 'exploring book styles' actually is" >}}

Suppose you run a large bookstore and want to understand the tone of every book you sold over the past year. Every book already has a category, of course — English certification prep, programming, natural science, and so on — but that categorization is too coarse. What you actually want to know is something finer: within "programming," are customers buying beginner tutorials, or advanced architecture-design books?

If business was terrible last year and you only sold 10 books, that's easy — just read all ten and you'll know your customers' taste. But what if you sold over 1,000? Nobody has time to read them all. This is exactly where machine learning comes in — letting a model sort out the underlying styles hiding in those 1,000 books for you.

Here's the approach: assume every book comes with a summary that roughly captures its content. We feed all 1,000 summaries into a model and let it explore the styles within them, grouping books with similar styles into the same cluster.

There are two key terms worth pinning down here, because they determine what kind of model comes next:

- **Unsupervised Learning**: throughout this process, we only feed in summaries — we never labeled any summary in advance as "this one's a hardcore technical book" or "this one's light pop-science." The model discovers the styles entirely on its own. Because no correct answer (label) is ever given to the model, this is Unsupervised Learning.
- **Clustering**: what the model has to do is uncover the underlying relationships between books and group the more closely related ones together — that's clustering.

## Step 2: Prepare Dataset

Once the problem is defined, the next step is preparing the data. This stage can be broken down into a few parts:

- **Data Collection**
  There are many ways to go about this — you could hire part-time workers to type up each book's summary, or scrape these summaries off the web with a crawler.

- **Data Exploration and Data Cleaning**
  This stage is about deeply understanding the data you've collected and turning it into a form suitable for feeding into a model. What we have on hand is "summaries," made up of many sentences, and those sentences often carry a bunch of elements that don't help with judging style, which can be stripped out first. For English text, common cleaning steps include:

  - Removing punctuation (`,` `.` `!` `?`)
  - Removing unimportant words (a, an, the)
  - Converting uppercase to lowercase (White => white)
  - Normalizing verb tense to present tense (did => does)

  After cleaning, there's one last step: a model can't consume text directly, so the data has to be converted from "string type" to "numeric type" before it can be fed in — this process is called **Data Vectorization**.

{{< image src="text-preprocessing.jpg" alt="A diagram illustrating the text preprocessing pipeline." caption="Preprocessing text" >}}

## Step 3: Model Training

With the dataset ready, next comes building and training the model. In the first step, we already established that "exploring book styles" is a clustering problem, and the most common model for solving clustering problems is **K-Means**. The math behind K-Means is beyond the scope of this article — for now, it's enough to understand what it actually does.

{{< image src="k-means.jpg" alt="A diagram of K-Means clustering results, showing k=2 on the left and k=3 on the right." caption="How the K-Means algorithm works" >}}

As shown above, each point represents one book's summary (i.e., the numeric vector produced by Data Vectorization). The K-Means model can split these points into multiple clusters. The "k" in K-Means' name is simply "how many clusters to form": setting k=2 splits all the points into two clusters (left above), while setting k=3 splits them into three (right above).

In other words, k is a parameter we have to decide ourselves, and how good the clustering result is depends heavily on whether we picked the right k.

## Step 4: Model Evaluate

So what should k be set to? That's exactly the question the model evaluation stage has to answer. We want to find the number of clusters that best groups all the similarly-styled books together — too few clusters, and different tones get forced together; too many, and the same style ends up fragmented across several clusters.

There are many statistical metrics for evaluating clustering quality; the one used here is the **silhouette coefficient**. It measures how close each point is to the other points in its own cluster, relative to how close it is to the neighboring cluster — the higher the value, the cleaner the clustering.

{{< image src="find-k-in-k-means-algorithm.jpg" alt="A chart of silhouette coefficient scores across different values of k." caption="Using the silhouette coefficient to find the best k for K-Means" >}}

By running each candidate k value and computing its silhouette coefficient, you can see which k the model performs best under. In the example above, the best k value turns out to be 19.

Once you've found the best k, you can go inspect the largest cluster — the one containing the most samples (books). Reading through that cluster's book summaries lets you see concretely what the most popular book style actually looks like — which is what the bookstore owner really wanted to know all along.

## Step 5: Model Inference

The last step is actually using this model. Feed in a new book's summary, see which cluster it gets assigned to, and you'll know which past batch of books it shares a similar tone with.

Running it the other way round is just as valuable: pick a cluster, pull out the book summaries inside it, and read them to understand what trait those books actually share that made the model group them into the same style. A clustering model won't name each cluster for you — that part of the interpretation still has to be done by a human.

## Conclusion

This article walked through the five-step machine-learning workflow using "exploring book styles" as an Unsupervised Learning example: starting from defining the problem as a clustering task, cleaning and vectorizing the text summaries, running **K-Means** to cluster them, using the **silhouette coefficient** to pick the best k, and finally using the model to interpret book styles.

Compared to the previous post's house price prediction, the process is identical — the only difference is that there's no label to work with, so both the model and the evaluation metric had to change. The next article will introduce a more powerful model (Neural Network) for tackling harder problems.
