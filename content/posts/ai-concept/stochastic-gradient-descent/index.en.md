---
# weight: 1
title: "An Introduction to Stochastic Gradient Descent"
date: 2026-07-09
lastmod: 2026-07-09
draft: false
description: "Why is plain gradient descent too slow for training a neural network? Learn how stochastic gradient descent uses mini-batches, and what batch size and epoch mean."
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

In the previous article, [Deep Learning Fundamentals: An Introduction to Gradient Descent](../gradient-descent/), we discussed how to update a parameter v with gradient descent so that the value of the cost function \( C(v_1, v_2, v_3, \dots) \) keeps decreasing. Computing the cost function's gradient gives us the parameter's "update direction", while setting the learning rate determines the "update size".

However, applying gradient descent directly to updating a neural network's parameters runs into a very practical problem: the parameters update far too slowly. Stochastic Gradient Descent is the improved version that exists to solve exactly this. This article explains what stochastic gradient descent is, how it differs from plain gradient descent, and what those frequently heard terms — mini-batch, batch size, and epoch — each actually mean.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Gradient descent's bottleneck**: the model must see the entire training set before it can compute a single gradient, and therefore before it can update the parameters even once.
- **What stochastic gradient descent does instead**: compute a gradient and update the parameters after seeing just one **mini-batch**, trading more frequent updates for faster training.
- **Batch size** is the number of training examples in a mini-batch. Like the learning rate, it is a hyperparameter you must set by hand.
- **The cost**: each step's direction becomes an estimate from a sample, so the batch size must not be too small — otherwise the direction is off and the model won't converge.
{{< /admonition >}}

## Updating a Neural Network's Parameters with Gradient Descent

Before getting into stochastic gradient descent, let's review how gradient descent updates the parameters inside a neural network.

As mentioned in [Deep Learning Fundamentals: The MNIST Dataset and the Cost Function](../mnist-and-cost-function/), the purpose of the cost function is to evaluate how good the network's current parameters (weights and biases) are: the smaller the cost, the closer this set of parameters brings the model's output to the correct answer.

{{< image src="Deep-Learning-Cost-Function.jpg" alt="The cost function takes a neural network's weights and biases and outputs a single value evaluating how good those parameters are." caption="Using a cost function to evaluate a neural network's parameters" >}}

And in [the article introducing gradient descent](../gradient-descent/), we already learned how to update a parameter v to drive the cost function's value down. For a neural network the procedure is exactly the same — just follow the same pattern, replacing v with the network's weights and biases:

{{< image src="gradient-descent-1.png" alt="The update equations for weight and bias, each subtracting the learning rate multiplied by the partial derivative of the cost function with respect to that parameter." caption="Following the same pattern to update a neural network's weights and biases" >}}

Each time this rule is applied, the weights and biases move one step in the direction that makes the cost function smaller. Repeat it enough times and the cost function's value keeps going down.

## The Drawback of Gradient Descent

Gradient descent is already a very usable method, but it has a structural drawback, and the problem lies in how the cost gets averaged.

The cost function mentioned above takes the form **\( C = \frac{1}{n} \sum_x C_x \)**, where **\( C_x \)** is the cost the model computes for a single training example (that is, the error between the model's output for that example and the correct answer). We sum the cost of every training example and divide by the number of training examples, giving the average cost per training example.

The gradient is computed the same way: first compute a gradient from a single training example's cost (\( \nabla C_x \)), then sum the gradients across all training examples and divide by the number of them, giving the average gradient per training example: **\( \nabla C = \frac{1}{n} \sum_x \nabla C_x \)**.

And that's exactly the problem: the model has to see the entire training set before it can compute one gradient, and therefore before it can update the parameters once. For a dataset like MNIST with 60,000 images, a full pass buys you a single parameter update — training obviously isn't going to be fast.

## What Is Stochastic Gradient Descent?

Stochastic gradient descent exists precisely to speed up training by making parameter updates more frequent. When updating parameters with it, the model doesn't need to see every sample in the training set before computing a gradient; instead it computes a gradient and updates the parameters after seeing just "some of the samples".

Here's a concrete example. Suppose the training set has 100 examples. With gradient descent, the model must see all 100 before it can compute one average gradient. With stochastic gradient descent, the model might compute an average gradient and update the parameters after only 10. For the same 100 training examples seen, the former updates the model **once**, while the latter updates it **ten times**.

You might ask: does it have to be 10? Would 20 or 5 work?

Of course they would. In stochastic gradient descent, this "subset of the data" is called a **mini-batch**, and the number of training examples in one mini-batch is called the **batch size**. Like the learning rate from the previous article, batch size is a hyperparameter — we (humans) must set it manually, and it cannot be updated automatically the way model parameters are.

How large the batch size should be is beyond this article's scope, but one principle is worth remembering up front. The reason we randomly draw a subset of the data to form a mini-batch is to update the parameters more often and speed up training. But if the "update direction" is wrong, no number of updates will make the model converge (that is, the cost function's value still won't come down). So the batch size must be large enough that the average gradient computed from this single mini-batch approximates the average gradient computed from the entire training set:

{{< image src="stochastic-gradient-descent-1.jpg" alt="Two expressions side by side showing the approximate relationship between the average gradient over an m-example mini-batch and the average gradient over the full training set." caption="The left-hand side is the average gradient computed from m training examples; the right-hand side is the average gradient computed from all training examples. The closer the left is to the right, the better" >}}

In other words, a mini-batch uses "a small sample" to estimate "the average gradient over the whole population". Sample too few, and the estimated direction drifts off.

## Updating a Neural Network's Parameters with Stochastic Gradient Descent

Back to the neural network. When updating with stochastic gradient descent, the weights and biases are updated like this:

{{< image src="stochastic-gradient-descent-in-neural-network.png" alt="The update equations for weight and bias, with the gradient term replaced by the sum of gradients over the m examples in a mini-batch, divided by m." caption="Updating a neural network's parameters with stochastic gradient descent" >}}

That is, each time we "randomly" draw one mini-batch of data from the whole training set — if the batch size is m, that's m examples. We sum the gradients of those m examples and divide by m to get the average gradient. With that average gradient we know the parameters' update direction, and the learning rate (the hyperparameter controlling "update size" mentioned earlier) then adjusts how big this step should be.

Once this weight and bias update is complete, we "randomly" draw another mini-batch from the training set and update the parameters the same way. When every example in the entire training set has been seen by the model once, the model has completed one **epoch** of training.

In practice, training a model runs for many epochs, and each epoch is split into many mini-batches. So "what you set the batch size to" directly determines how many times the parameters get updated within one epoch: the dataset size n divided by the batch size m is the number of updates in that pass.

## Conclusion

This article introduced stochastic gradient descent along with the concepts of mini-batch, batch size, and epoch. Its difference from gradient descent comes down to a single sentence: instead of updating the parameters only after seeing the entire training set, it updates after each mini-batch, trading more frequent updates for faster training.

The cost is that each step's direction is no longer "the average gradient over all the data" but an estimate from a sample. So the batch size must not be too small, or the direction goes off target and the model fails to converge. This trade-off between "update frequency" and "gradient accuracy" is the one you'll run into most often when tuning in practice.

### References

- [Neural networks and deep learning](http://neuralnetworksanddeeplearning.com/chap1.html)
- [Stochastic gradient descent – Wikipedia](https://en.wikipedia.org/wiki/Stochastic_gradient_descent)
- [深度學習中的 batch 大小對學習效果有何影響？ – 知乎](https://www.zhihu.com/question/32673260)
- [Difference Between a Batch and an Epoch in a Neural Network (machinelearningmastery.com)](https://machinelearningmastery.com/difference-between-a-batch-and-an-epoch/)
- [What is batch size in neural network? – Cross Validated](https://stats.stackexchange.com/questions/153531/what-is-batch-size-in-neural-network)
