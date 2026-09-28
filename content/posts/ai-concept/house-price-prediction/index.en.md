---
# weight: 1
title: "House Price Prediction: The Five ML Steps as One Complete Example"
date: 2022-02-03
lastmod: 2022-02-03
draft: false
description: "Having covered the five ML steps one at a time, this post runs house price prediction through all five end to end, from problem definition to training and inference."
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

This is the 8th article in the "Machine Learning Fundamentals" series. In the previous posts, we walked through the five steps of machine learning one at a time: [Define the Problem](../define-problem/), [Prepare Dataset](../prepare-dataset/), [Model Training](../model-training/), [Model Evaluate](../model-evaluate/), and [Model Inference](../model-inference/). Each of these five steps is simple enough on its own, but the part that actually trips people up in practice is figuring out how a real problem maps onto them.

So this post doesn't introduce any new concepts. Instead, it takes a classic example — house price prediction — and runs through all five steps from start to finish, so we can see exactly what each step is responsible for on a real task.

House price prediction is a popular beginner example because the goal is so intuitive: given the characteristics of a house, guess how much it's worth. If you already have the basic concepts down and want more hands-on practice, you can jump straight into Kaggle's [House Prices – Advanced Regression Techniques competition](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/overview) and sharpen these ideas on a real dataset.

## Step 1: Define the Problem

{{< image src="define-problem.jpg" alt="A diagram illustrating the 'Define the Problem' step of the five-step machine learning workflow." caption="Defining the problem" >}}

For house price prediction, we want a model that looks at a house's own "attributes" — number of bedrooms, number of bathrooms, floor area, location, and so on — and uses them to predict the house's price.

So what we need to collect is a batch of samples, where each sample represents one house and records that house's attributes along with its current sale price. Laid out, it looks roughly like this:

{{< image src="example-dataset.jpg" alt="A table of an example house price dataset, where each row is a house with columns for attributes like number of rooms and floor area, and the last column is the sale price." caption="An example house price dataset" >}}

With this table in hand, we can pin down what kind of problem this actually is. Since we already have the "price" for every single house, every row of data comes with its own correct answer attached — which makes this a **Supervised Learning** problem.

Next, look at what the model needs to output: a house price is a continuous number (12.8 million and 12.83 million are both valid answers), not a category like "expensive" or "cheap" — so this is a **Regression** problem, not a classification one. These two calls directly determine which models and which evaluation metrics come next, so it's worth spending real time getting this first step right.

## Step 2: Prepare Dataset

Once the problem is defined, the next step is getting the data into a shape the model can actually consume. This stage mainly covers the following:

- **Data Collection**
  There are many ways to get a dataset — the simplest is to find one that already exists online. [Kaggle Datasets](https://www.kaggle.com/datasets), for example, hosts a large number of datasets ready to train a model on directly.
- **Data Exploration / Data Inspection**
  The goal here is to understand the data better, especially the type of each attribute. If a column is a string (e.g., a location written as a district name), it has to be converted into numbers first before a model can take it as input.
- **Data Cleaning**
  During exploration, it's common to find samples with missing values — sample #043 might be missing its "price," sample #103 might be missing its "floor area." You can fill in the missing values with some statistical method, or simply drop that sample from the dataset entirely.
- **Summary Statistics** and **Data Visualization**
  After cleaning, use statistical measures to summarize the dataset as a whole, or plot the distribution of the samples, to get an intuitive feel for the data you're working with.

## Step 3: Model Training

Once the dataset is ready, it's time to build the model and start training. Before training begins, the whole dataset is usually split into a "training set" (80%) and a "testing set" (20%), so that some data the model has never seen is kept aside for a fair evaluation of its prediction quality afterward. If everything goes into training, the model is only ever tested on questions it has already memorized — a high score there doesn't mean much.

Back in the problem-definition step, we already established that house price prediction is a regression problem, so naturally we train a **Regression Model** here.

There's no shortage of tools for building a regression model: for a traditional machine-learning approach, [scikit-learn](https://scikit-learn.org/stable/) works well; for a deep-learning approach, [TensorFlow](https://www.tensorflow.org/) or [PyTorch](https://pytorch.org/) are the usual picks.

## Step 4: Model Evaluate

Once training is done, it's time for the "testing dataset" we deliberately held back earlier to step in and evaluate how good the model actually is. As covered in the [Model Evaluate](../model-evaluate/) article, classification models and regression models each come with their own set of evaluation metrics to choose from.

House price prediction is a regression problem, and the common evaluation metrics are **MAE (Mean Absolute Error)**, **MSE (Mean Squared Error)**, and **RMSE (Root Mean Squared Error)**.

{{< image src="common-loss-function-for-regression.jpg" alt="A comparison of the formulas for MAE, MSE, and RMSE, common loss functions for regression problems." caption="Common loss functions for regression problems" >}}

This series won't dive into the underlying math, but the intuition alone is enough to work with: whether it's MAE, MSE, or RMSE, they're all measuring the same thing — how far the model's "predicted value" is from the actual "correct value." The smaller the gap, the more accurate the model's predictions.

## Step 5: Model Inference

Once the model has been evaluated and its quality judged acceptable, it's ready to actually predict house prices. Feed in samples the model never saw during training, and get back its predicted values — that's model inference. Only at this point does the work from the previous four steps actually turn into something usable.

## Conclusion

This article used "house price prediction" as an example to walk through the five steps of machine learning once more, and to see what role each step plays in solving a real task: defining the problem established this as a regression task within supervised learning, preparing the dataset turned raw data into something the model could consume, training and evaluation produced and validated the model, and finally inference put the model to work.

House price prediction is an example of supervised learning. [The next article](../book-clustering/) will apply the same five steps to a real-world example of "unsupervised learning" instead.
