---
# weight: 1
title: "Machine Learning in 5 Steps: How to Evaluate a Model"
date: 2023-02-02
lastmod: 2023-02-02
draft: false
description: "Once training is done, how do you know a model is any good? A look at model evaluation, what overfitting is, and the metrics used for classification and regression tasks."
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

As soon as model training finishes, a very practical question pops up: is this model actually any good? Answering that question is the job of the fourth step in the machine learning pipeline, **Model Evaluation**.

This is the sixth article in the machine learning fundamentals series. The previous article, [Machine Learning Problem-Solving in 5 Steps: Model Training](../model-training/), covered how a model is trained and the common types of models. This one picks up from there: how do we quantify a model's performance after training, what exactly is overfitting, and which evaluation metrics apply to classification versus regression tasks.

{{< image src="machine-learning-process-1.jpg" alt="Diagram of the five-step machine learning workflow, highlighting the fourth step, Model Evaluation, as the current stage." caption="Step four of solving a problem with machine learning: Model Evaluation" >}}

## The Idea Behind Model Evaluation

In the earlier [dataset preparation](../prepare-dataset/) step, we split the data we had into a training set and a test set. Only the training set is fed to the model during training; when it comes time to evaluate, we deliberately switch to the test set — the portion the model has never seen from start to finish.

Why does it have to be data the model has never seen? An exam analogy makes this easiest to understand. Doing a pile of practice problems before the exam is like the model's "training" phase; exam day itself is the "evaluation" phase, where a set of problems you've never seen before is used to check what you actually learned from practicing. The exam questions are usually similar in style to the practice problems, so as long as you genuinely understood the concepts while practicing, you should at least pass.

Conversely, if you only memorized the practice problems — question and answer together, as a set — you'll be stumped the moment the exam phrases something differently, since the odds of the exact same question showing up again are low.

Models can fall into the same trap. A model that performs beautifully during training but falls apart during evaluation is said to be **overfitting**: it never actually learned how to solve the problem from the training data, it just memorized the answers. Evaluating with test data the model has never seen is exactly how we catch this.

## Common Metrics for Classification Tasks

To call a model "good" or "bad," we first need a metric that produces an actual score. Sticking with the exam analogy: imagine an exam made entirely of true/false questions, where a teacher grades each one as either fully correct or fully wrong — there's no partial credit — so the score for the whole exam comes down to how many questions were answered correctly.

Classification models work the same way. Take image classification as an example: every image has exactly one correct category, and dividing the number of images the model classified correctly by the total number of images gives you **Accuracy**. If a model classifies 92 out of 100 images correctly, its Accuracy is 92%.

Besides Accuracy, **F1 Score** is another common metric for classification tasks, which a later article in this series will cover in more detail.

## Common Metrics for Regression Tasks

As mentioned in [Machine Learning in 5 Steps: How to Define the Problem](../define-problem/), common machine learning tasks fall into two categories: classification and regression. Classification lets you count right and wrong answers, but a regression model outputs a continuous value with no clean notion of "correct" or "incorrect" — so how do you evaluate it?

The more intuitive approach is to look at how far off the prediction is from the true value. For example, if a regression model predicts a house price of 12,300 when the true price is 15,000, the error for that one sample is | 12300 – 15000 | = 2700.

Take the absolute value of the error for every sample, sum them up, and divide by the total number of samples, and you get an average error called **Mean Absolute Error (MAE)**. A common variation is to square each sample's error instead of taking its absolute value before averaging, which gives you **Mean Square Error (MSE)**.

## Evaluation Metrics in scikit-learn

In practice you don't need to implement any of these metrics yourself — scikit-learn already ships ready-to-use implementations. The two figures below list the metrics scikit-learn commonly uses to evaluate regression and classification models, respectively:

{{< image src="loss-function-for-regression.jpg" alt="Overview table of commonly used evaluation metrics for regression tasks in scikit-learn." caption="Common loss functions for regression [source: scikit-learn]" >}}

{{< image src="loss-function-for-classification.jpg" alt="Overview table of commonly used evaluation metrics for classification tasks in scikit-learn." caption="Common loss functions for classification [source: scikit-learn]" >}}

For the full list and an explanation of each metric, see the [Model evaluation section of the scikit-learn documentation](https://scikit-learn.org/stable/modules/model_evaluation.html#the-scoring-parameter-defining-model-evaluation-rules).

## Conclusion

{{< image src="machine-learning-process-2.jpg" alt="Diagram of the five-step machine learning workflow, with an arrow showing the loop back to earlier steps when evaluation results are poor." caption="If the evaluation results aren't good, the problem may lie in one of the earlier steps" >}}

This article introduced the idea of Model Evaluation: using test data the model has never seen to check what it actually learned during training, and choosing metrics appropriate to the task type — Accuracy for classification, and MAE or MSE for regression. We also covered overfitting, the case where a model memorizes the training data and, as a result, performs poorly during evaluation.

When evaluation results aren't good, the problem isn't necessarily in the evaluation step itself — more often something went wrong earlier: the problem definition may need revisiting, the dataset may need rebuilding, or the model may need retraining. Before moving on to the next step, "using the model," these first four steps typically get run through several times, until the model reaches a good enough quality.
</content>
