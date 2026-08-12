---
# weight: 1
title: "How to Build a Dataset for Machine Learning (in 4 Steps)"
date: 2023-01-28
lastmod: 2023-01-28
draft: false
description: "Data preparation eats up roughly 80% of a machine learning project's time. Learn its four stages: collection, inspection, summary statistics, visualization."
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

This is the fourth post in the "Machine Learning Fundamentals" series. The previous article, [The Five Steps to Solving Problems with Machine Learning: Defining the Problem](../define-problem/), walked through the full five-step framework and unpacked the first step, "defining the problem," in detail — getting a clear picture of what task you're actually solving is what gives every later step a direction.

This post moves on to the second step: **building a dataset**. It covers two things: why this step carries far more weight than it seems to at first glance, and the four stages you actually go through when doing it.

## Why building a dataset matters

{{< image src="machine-learning-five-steps.jpg" alt="A diagram of the five steps to solving a problem with machine learning, with the second stage, 'building a dataset,' highlighted" caption="Step two of solving a problem with machine learning: building a dataset" >}}

"Building a dataset" is arguably the single most important of the five steps. If you want to solve a problem with machine learning, you have no choice but to prepare data — and the quality of that data is directly reflected in the quality of the model you end up training.

The logic here is fairly intuitive: a model learns its patterns from data, so if the data itself has problems, the model learns those problems right along with everything else. Keep the same algorithm and the same hyperparameters, swap in a cleaner dataset, and the results can look completely different.

{{< image src="data-preprocessing-in-ml.jpg" alt="A chart showing how much time each stage of a machine learning project takes, with data preparation taking up the vast majority" caption="Dataset preparation and preprocessing take up the bulk of a machine learning project's time" >}}

According to commonly cited statistics, "data preparation" accounts for close to 80% of the time spent solving a task with machine learning, while every other step combined takes up just 20%. That alone tells you how important — and how far from simple — the data preparation process really is.

Flip that number around: the time actually spent tuning the model is a small slice of the whole project. When you're new to the field it's easy to assume the real action is in the algorithms. Once you've been through a project or two, you realize most of the effort actually goes into getting the data into a usable state.

## The steps of building a dataset

{{< image src="prepare-dataset-in-ml.jpg" alt="A diagram of the four steps involved in preparing a dataset" caption="Preparing a dataset in machine learning involves four steps" >}}

The process of building a dataset breaks down into these four steps:

- Data Collection
- Data Inspection
- Summary Statistics
- Data Visualization

If you want to train a high-quality machine learning model, the quality of your data matters enormously. Let's walk through what each of these steps means, in order.

## Data Collection

Data Collection is exactly what it sounds like: gathering data. Depending on the task, this step can be trivially easy or extremely hard — the gap is huge.

In the lucky case, someone has already put together a ready-made dataset for your task, and you can simply download it. If nothing suitable already exists, you may need to write a "crawler" to scrape large amounts of data from the web yourself, or even label it by hand.

The key question at this stage is: **does the data you collected actually match the machine learning task you defined in the previous step?** No amount of data helps training if it doesn't line up with the task.

## Data Inspection

Data Inspection means checking your data. As mentioned above, data quality has a direct effect on the model, and open-source datasets found online vary wildly in quality — so they need to be inspected before you use them to train a model.

Data inspection typically looks at three things:

- Outliers in the dataset
- Missing values in the dataset
- Whether the data needs preprocessing before it can be fed into a model

To make this concrete: if a user-data record has an "age" field of 999, that's almost certainly an outlier. If some records have fields that are simply empty, that's a missing value. Feed either of these straight into a model without handling them, and the patterns the model learns will inevitably be skewed.

The specific fixes for each of these three problems vary by task, and will be covered in future articles.

## Summary Statistics

The idea behind Summary Statistics is: run statistical analysis over data you've already processed. A handful of statistical metrics is enough to give you an initial read on your dataset.

Think mean, median, max and min, and standard deviation. These are all basic statistical measures, and their job is simply to give you a first sense of how the values in your dataset are distributed.

Even just these few numbers can often reveal something is off. A large gap between the mean and the median usually means the distribution is being pulled by a handful of extreme values; an unreasonably large standard deviation is also a signal worth going back and checking the data over.

## Data Visualization

{{< image src="data-visualization.jpg" alt="A collage of several types of data visualization charts, including bar charts, line charts, and pie charts" caption="Visualizing data through a variety of chart types [source: FineReport]" >}}

Data Visualization does exactly what it says: it turns data into pictures using various types of charts. Once visualized, data stops being a wall of raw numbers and becomes a set of meaningful charts.

After visualization, it becomes much easier to spot outliers or trends. This is also where it complements the previous step, Summary Statistics: statistics compress an entire dataset down into a few numbers, while charts lay the shape of the distribution out in full — and some problems are simply faster to catch by eye than by calculation.

## Conclusion

This article introduced the second of the "five steps to solving problems with machine learning" — building a dataset — and broke it down into its four stages: Data Collection, Data Inspection, Summary Statistics, and Data Visualization.

There's really just one thing to remember: preparing a dataset is the most important, and the most time-consuming, step in the whole process, and the quality of that data has an outsized effect on the model you end up training. The next article moves on to the third step, [model training](../model-training/).
