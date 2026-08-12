---
# weight: 1
title: "Model Inference: The Final Step in the Machine Learning Workflow"
date: 2023-02-05
lastmod: 2023-02-05
draft: false
description: "The last step in the ML workflow is model inference: deploying a trained model and running predictions. See how it differs from training, plus Pruning and Quantization."
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

This is the seventh article in the "Machine Learning Fundamentals" series. We've already walked through [defining the problem](../define-problem/), [building a dataset](../prepare-dataset/), [model training](../model-training/), and [model evaluation](../model-evaluate/). This article covers the final step: model inference.

The first time many people hear this term, it sounds almost redundant — the model is already trained, so can't we just move it onto a machine and run it? This article explains why that's not quite so simple. We'll first look at what model inference actually means, then compare it to model training, and finally cover the two most common optimization techniques used in practice: Pruning and Quantization.

## The Meaning of Model Inference

{{< image src="model-inference.jpg" alt="A diagram showing input data flowing into an already-trained model, which directly outputs a prediction." caption="Model inference is simply using a trained model to make a prediction" >}}

Model inference refers to the process that happens after a model has already been trained and evaluated, and has been deployed onto real target hardware: data is fed into the model, and the model produces a prediction. In other words, this is the stage where the model actually "goes to work."

A useful everyday analogy: model inference is like a soldier who has gone through extensive training and passed every test, and can now finally operate independently on the battlefield.

At this point you might still be wondering — during model training, we also feed samples into the model and also get predictions back. So once training is done, doesn't simply "copying" the model onto a target device count as inference?

## The Difference Between Model Training and Model Inference

{{< image src="model-training-vs-model-inference.jpg" alt="A side-by-side comparison diagram contrasting the workflows of the model training stage and the model inference stage." caption="Model Training vs. Model Inference" >}}

Not quite. Model training is focused on minimizing a loss function to find the best set of parameters for the model. The model at this stage can be fairly complex, containing thousands upon thousands of parameters. Training also typically runs on machines with ample resources, where spending a bit more memory or a few more hours is well within an acceptable range.

Model inference has an entirely different focus: deploying the model onto target hardware or a production line, and actually applying it to solve the problem. Since the model is now being used in a real-world setting, its size and computational cost have to be taken seriously, because both directly affect memory usage, computation time, and power consumption.

| | Model Training | Model Inference |
|---|---|---|
| Goal | Minimize the loss function to find the optimal parameters | Apply the model in practice to produce predictions |
| Execution environment | A resource-rich training machine | Target hardware, devices on a production line |
| Top priority | Model accuracy | Model size, computation speed, power consumption |

For example, if we train a "face recognition" model and deploy it on a drone, the model's computation must not drain too much power, in order to preserve the drone's flight time. Or if we deploy a model onto a self-driving car, the model's computation speed absolutely has to be fast enough — a one-second delay could cause an accident. The same model placed on different hardware runs into completely different constraints, and that's the real difficulty of the inference stage.

So model inference isn't just about feeding in data and producing a prediction — the model's performance, speed, and power consumption also need to be optimized. Two common optimization methods are Pruning and Quantization.

## Pruning and Quantization

Here's a brief explanation of both concepts. If you'd like to go deeper into optimizing a model's performance, speed, and power consumption, check out [TensorFlow's official documentation](https://www.tensorflow.org/model_optimization/guide).

- **Pruning**: short for Weight Pruning. By observing which parameters in a model have little impact on its predictions, those parameters are removed to reduce the model's complexity and computational cost. Conceptually, it's a lot like packing luggage — pull out the things you'll barely use, and the suitcase gets lighter.
- **Quantization**: if a model's parameters are stored as 32-bit floating point numbers, they get converted to 8-bit. By reducing the "precision" of the model's parameters, this shrinks the model's size and speeds up computation.

Whether it's Pruning or Quantization, the goal is always the same: simplify the model, speed up computation, and reduce energy and time costs, all while keeping the model's original prediction accuracy intact. The tricky part is that "all while" — shrinking a model is easy; shrinking it without losing much accuracy is hard, which is why both techniques require a lot of trial-and-error tuning in practice.

## Conclusion

This article introduced the concept of model inference and compared it with model training: the former cares about running the model fast and lean, the latter cares about learning good parameters. We also covered two model optimization techniques, Pruning and Quantization.

The next article will walk through a complete end-to-end example, revisiting all five steps: defining the problem, building a dataset, model training, model evaluation, and model inference.
