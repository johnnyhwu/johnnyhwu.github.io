---
# weight: 1
title: "Estimation Error vs. Approximation Error: Architecture or Training?"
date: 2022-05-29
lastmod: 2022-05-29
draft: false
description: "Is a model's inaccuracy from an architecture that can't reach the answer, or training that fell short? This splits its error into approximation and estimation error."
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

In [Machine Learning Basics: The Bias-Variance Tradeoff](../bias-variance-tradeoff/), we split a model's error into two pieces: bias error and variance error. A model with high bias is called underfitting; one with high variance is called overfitting.

This post looks at the same thing from a different angle. "The model isn't accurate enough" can still be asked in a different way first: is the error there because the model's architecture simply can't reach the answer, or because training never got the model to where it should have gone? The first is called approximation error, the second estimation error. It's worth being comfortable with the bias-variance tradeoff before reading on, since the two ideas end up connected.

## Training a Model

Let's start with a workflow everyone has gone through. Suppose we want a perfect model that can classify cat and dog pictures with 100% accuracy — a fairly basic binary classification problem, usually trained with supervised learning.

Before training, we first have to build a model. The architecture's design varies from person to person — maybe a 5-layer CNN followed by fully-connected layers. At this point the model's parameters might be random, or initialized from some probability distribution; either way, the model can't yet tell cats from dogs.

Next we take a prepared dataset and start training. During training, the model's internal parameters keep getting adjusted, and its error keeps dropping. We stop once we're satisfied, ending up with a trained model. That model's internal parameters are now completely different from where they started, and it can correctly classify most cat and dog images.

{{< image src="best-function.jpg" alt="Diagram showing the relationship between the function class, the best function, and the learned function." caption="The relationship between the function class, the best function, and the learned function" >}}

The description above actually walked through three steps:

- Wanting a perfect model
- Building a model
- The trained model

These three steps map directly onto every element in the figure above. The "perfect model" we hoped for is the **best function** in the diagram. When we "build a model," we can design different architectures, and the parameters inside that architecture have infinitely many possible values — that whole space of possibility is the **function class** in the diagram. Once training finishes and the parameters settle, the resulting "trained model" is the **learned function**.

In other words, deciding on a model's architecture is really drawing a boundary around one region of all possible functions; training is picking a single point inside that region.

## Estimation Error and Approximation Error

The figure above shows that there's still a substantial gap between the learned function and the best function. That gap can be split into two parts: estimation error and approximation error.

{{< image src="function-class.jpg" alt="Diagram marking a green point closest to the best function within the function class." caption="The relationship between the function class, the learned function, and the best function" >}}

In the figure above, we've added a "green point," representing the function within our defined function class that's closest to the best function. It represents the limit this architecture could reach under the best possible circumstances — even if training were flawless, it could only get this far.

{{< image src="approximation-error-and-estimation-error.jpg" alt="Diagram using the green point as a boundary to mark the approximation error and estimation error distances." caption="Approximation error and estimation error" >}}

With the green point as the boundary, the two errors become easy to define:

- **Approximation error**: the distance from the green point to the best function. This gap comes from the model's architecture itself and has nothing to do with how well it was trained.
- **Estimation error**: the distance from the green point to the learned function. This gap comes from training failing to bring the model all the way to where it should have gone.

If we define an extremely complex model — a very large function set, large enough to fully contain the best function — then approximation error becomes zero, but estimation error may grow larger instead. The region is too big, so finding the best point inside it during training gets harder. Conversely, if we define an extremely simple model — a very small function set — estimation error will be small, but approximation error will become large: the region is small enough to search easily, but the answer simply isn't inside it.

Doesn't the relationship between approximation error and estimation error look exactly like the bias-variance tradeoff? The more complex the model, the smaller the error from its architecture and the larger the error from training — the two move in opposite directions. This is the same tradeoff, just described in a different vocabulary.

## References

- [Stanford CS221 Lecture 3](https://web.stanford.edu/class/archive/cs/cs221/cs221.1186/lectures/learning3.pdf)
- [Estimation versus approximation error](https://mlweb.loria.fr/book/en/estimationapproximationerrors.html)
- [What does the term "Estimation error" mean?](https://stats.stackexchange.com/questions/87750/what-does-the-term-estimation-error-mean)

## Conclusion

This post introduced a model's estimation error and approximation error: treating the point in the function class closest to the best function as a boundary, with the architecture's limit on one side and training's shortfall on the other. As a model gets more complex, approximation error falls and estimation error rises.

Next time you resize a model and don't see the improvement you expected, try thinking about it from this angle: is the problem that the architecture can't reach the answer, or that training never got there? The answer changes what you should actually go and fix.
