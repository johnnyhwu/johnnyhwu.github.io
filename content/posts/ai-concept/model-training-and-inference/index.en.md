---
# weight: 1
title: "Model, Training, Inference: A Pottery Wheel Analogy"
date: 2022-01-21
lastmod: 2022-01-21
draft: false
description: "Model, training and inference are three views of one idea. This article uses a pottery-wheel analogy and a house-price example to explain what each term means."
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

In the world of machine learning, "model," "model training algorithm," and "model inference algorithm" are three terms you keep running into over and over. This article walks through all three from the ground up: what a model actually is, what the computer is really doing while it "trains," and how we use the model once training is done.

If you don't already have a basic sense of what machine learning is, it's worth reading the previous article in this series, [What Is Machine Learning?](../what-is-machine-learning/), first — everything below assumes you roughly know what machine learning is trying to do.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Model**: a function with parameters — it takes one thing in and produces another thing out.
- **Training**: repeatedly adjusting the model's parameters until its output reaches a level we're happy with.
- **Inference**: using the trained model to make predictions on data it has never seen — the stage where a model actually earns its keep.
- **How the three relate**: they aren't three separate things, but the same model seen at three different stages — like throwing pottery: the clay, the shaping, and testing the finished piece.
{{< /admonition >}}

## How model, training and inference relate

Anyone encountering machine learning for the first time tends to get scared off by a wall of jargon. So before getting into any math, here's an everyday analogy that ties the three concepts together: throwing pottery on a wheel.

A "model" is like a lump of clay that hasn't been shaped yet. "Training" is the process of shaping that clay with your hands — and because different goals call for different shaping techniques, machine learning ends up with just as many different training algorithms. "Inference," meanwhile, is like testing the finished, fired vessel: you pour some liquid in and confirm it actually holds up.

{{< image src="machine-learning-process.jpg" alt="A diagram of the machine learning workflow, showing the model, training, and inference steps in sequence." caption="Machine learning is mainly divided into these three steps [source: Udacity]" >}}

In other words, these three aren't independent things — they're the same model shown at different stages.

## What a machine learning model actually is

Looked at another way, in mathematical terms a model is simply a "function." Yes, the same y = f(x) you learned back in school. The idea behind a function is simple: feed something in, get something else out.

Different problems call for different functions. For example, the diagram below is a function: it takes a picture as input and outputs that picture's category.

{{< image src="machine-learning-function.jpg" alt="A diagram showing a picture as input, passing through a function, with the picture's category as output on the right." caption="In machine learning, a model is a function: input a picture, output that picture's category" >}}

Or take this function instead: it takes a house's square footage as input and outputs that house's price. This example will run through the rest of the article, so it's worth remembering.

{{< image src="machine-learning-function-1.jpg" alt="A diagram of a function taking a house's square footage as input and outputting that house's price." caption="In machine learning, a model is like a function: input a house's square footage, output that house's price" >}}

Since a model is a function, it naturally has parameters. For instance, the function below contains three parameters, \( w_1 \), \( w_2 \), and \( w_3 \). These parameters are what the model has actually "learned" — keep the same function shape but swap in a different set of parameters, and you get an entirely different model.

{{< image src="machine-learning-function-2.jpg" alt="A function diagram with three internal parameters labeled w1, w2 and w3." caption="In machine learning, a model is like a complex function containing the parameters \( w_1 \), \( w_2 \), and \( w_3 \)" >}}

Back to the house-price example. To train a model that takes "square footage" in and outputs "price," we prepare a large number of samples for the model to learn from, where each sample contains two values: (square footage → price).

{{< image src="linear-regression-model.jpg" alt="A 2D scatter plot with blue dots for square footage vs. price samples and a red line for the fitted model." caption="The red line is the model we hope to learn" >}}

Plotting all of these (square footage → price) samples on a two-dimensional plane gives us the blue dots in the diagram. We want the model to automatically adjust its own parameters using these blue dots, so that after we feed in a square footage, it outputs a sufficiently accurate price. In other words, the red line in the diagram is the model we're hoping to end up with.

## What training a model actually is

The process by which "a model learns to adjust its own parameters" is what we call training the model.

Training is a loop that repeats over and over, and each round involves two actions:

- Figuring out the direction and size of the adjustment to make to the model's parameters
- Actually adjusting those parameters

We repeat these two actions until the model's output reaches a level we're satisfied with.

{{< image src="linear-regression-model-1.jpg" alt="Three side-by-side linear regression diagrams, with the red line gradually going from horizontal to fitting the blue sample points." caption="The model gradually goes from (1) to (3)" >}}

Take the "input square footage, output price" model as an example. At the very start, the model might just be a flat, horizontal line (1) — no matter what square footage you feed in, it spits out the same price every time, which is obviously useless. After one round of parameter adjustment, it becomes a slightly tilted line (2): the bigger the square footage, the bigger the output price, so the output is starting to make sense. As the parameters get adjusted more and more times, the price predictions keep getting more accurate, and eventually it becomes the model we actually want (3).

## What inference on a model actually is

Once a model has finished training, its internal parameters have already been adjusted many times, and its output reaches a satisfying level across different inputs. What comes next is the inference stage. Put simply, inference means we now formally start "using the model."

{{< image src="model-inference.jpg" alt="An inference diagram, where a sample with only square footage is fed in and the model outputs the corresponding predicted price on the red line." caption="Feed in a house's square footage, and the model outputs a predicted price" >}}

In the "input square footage, output price" example, the model saw the blue samples in the diagram during training, and after many rounds of parameter adjustment it has become the current model (the red line). In the future, whenever we get a sample that only has square footage and no price, we can feed it into this trained model and get back a predicted price (the red dot). This is also the stage where the model actually delivers value: training happens only once, but inference gets used over and over, countless times.

## Conclusion

This article walked through model, model training, and model inference in machine learning: a model is a function with parameters, training is the process of repeatedly adjusting those parameters, and inference is using the trained model to predict data it has never seen.

The next article picks up from here and looks at, when we run into a problem that needs machine learning to solve it, [what steps to follow to define the problem clearly](../define-problem/) before solving it step by step.
