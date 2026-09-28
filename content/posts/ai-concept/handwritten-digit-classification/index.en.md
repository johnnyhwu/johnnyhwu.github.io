---
# weight: 1
title: "Why a Digit Classifier Needs 10 Output Neurons, Not 4"
date: 2026-06-14
lastmod: 2026-06-14
draft: false
description: "A digit classifier's output layer uses 10 neurons, not the sufficient 4. Seeing why means stepping into the network's own eyes to watch how it reads an image."
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

In the [previous article, "Deep Learning, Step One: Neural Network Terminology,"](../what-is-neural-network/) we met a neural network's basic components, the design thinking behind its input and output layers, and the difference between a feedforward neural network and a recurrent neural network.

This article takes a different angle and starts from a very concrete problem: handwritten-digit image classification. We'll actually design a neural network that can solve it, then step into the network's own point of view and see exactly how it "reads" the digit inside an image.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **The problem**: classify a 28 × 28 grayscale image of a single handwritten digit (0-9).
- **The design**: a 784-neuron input layer (one neuron per pixel, normalized to 0.0-1.0), one hidden layer of 15 neurons, and a 10-neuron output layer, one neuron per digit.
- **Why 10 output neurons, not 4**: 4 neurons could technically encode 16 values as bits, which is plenty for 10 digits — but experiments show 10 neurons classify better, and the reason becomes clear once you see how the hidden layer represents shape features.
- **How the network "sees"**: each hidden-layer neuron specializes in one local feature (a stroke in one corner of the image) through its own weights, and the output layer combines those features into a final classification.
{{< /admonition >}}

## The Handwritten-Digit Classification Problem

Handwritten-digit image classification is one of the most common problems in deep learning, and it's often the very first project for people just starting out. The reason is simple: the problem is small enough to reason through every step in full, yet it still keeps the complete shape of an image-classification problem.

{{< image src="handwritten-digit-sample.jpg" alt="A row of handwritten Arabic numerals, reading 504192, with the strokes running together." caption="A sample handwritten-digit image [source: Neural Networks and Deep Learning]" >}}

The image above is one handwritten-digit image. We want to train a neural network that can accurately recognize each digit inside it — that is, 504192. For an image like this, recognition breaks down into two steps: first, segment the image so each digit is separated out; second, classify each individual digit image (0-9).

This article doesn't cover the first step, segmentation. We'll focus entirely on the second step, classification. From here on we'll assume every image contains exactly one digit, and that every image is the same size (28 × 28). So how should we design a neural network to recognize that digit?

## Designing the Neural Network

We already touched on this question in the earlier article about a neural network's components. For this specific problem, the design of the input and output layers can actually be worked out quite intuitively.

{{< image src="neural-network-architecture.jpg" alt="A three-layer neural network diagram: a large number of input neurons on the left, one hidden layer in the middle, and 10 output neurons on the right." caption="Designing the neural network [source: Neural Networks and Deep Learning]" >}}

As shown above, every neuron in the input layer stands for the value of a single pixel in the image. Since every image is 28 × 28, that's 784 pixels total, so the input layer has 784 neurons (the diagram above doesn't literally draw all 784, for space).

Also, because every image is grayscale, each pixel has just one channel, representing "how black" that pixel is. A pixel value of 0 means "pure white," 255 means "pure black," and anything in between is a shade of gray mixed from the two.

That said, we don't usually feed a pixel's raw value straight into the neural network. To speed up training and improve its quality, we conventionally compress the input values down to the 0-1 range first, by dividing each pixel value by 255 so every input neuron's value ends up between 0.0 and 1.0. This step is called normalization, and [this Stack Overflow thread](https://stackoverflow.com/questions/4674623/why-do-we-have-to-normalize-the-input-for-an-artificial-neural-network) has a good rundown of why it matters.

As for the middle of the network, the diagram above uses just one hidden layer, containing 15 neurons.

The output layer contains 10 neurons, one for each digit 0 through 9. For example, after feeding in an image, if the neuron representing the digit 6 produces the largest value, that means the neural network believes the image is a "6."

## Why Not Just Use 4 Output Neurons?

Since the output layer ultimately just needs to represent one of the digits 0-9, why not use 4 neurons instead? Each neuron can represent 0 or 1, so 4 neurons can represent 2 × 2 × 2 × 2 = 16 possible values — plenty of room for 10 digits, with 6 neurons to spare.

Answering this properly isn't easy, because it means putting ourselves in the neural network's shoes and understanding how it actually reads the information in an image. Before we get there, though, here's a more practical answer: experiments confirm that a 10-neuron output layer classifies better than a 4-neuron one.

## How the Neural Network Understands the Image

Let's get a feel for how the neural network understands the information in an image. We'll focus on the first neuron in the output layer — the one responsible for "outputting 0." Assume this network has already finished training. When we feed in an image of a handwritten "0," this neuron should produce a larger value than every other neuron in the output layer.

{{< image src="neural-network-architecture.jpg" alt="The same neural network diagram, with focus on the neuron at the top of the output layer, responsible for outputting the digit 0." caption="Focusing on the first neuron in the output layer [source: Neural Networks and Deep Learning]" >}}

What this neuron does, at bottom, is take the output of every neuron in the hidden layer, multiply each by its own weight w, and add them all up. So what is the hidden layer's job?

Every neuron in the hidden layer is responsible for detecting one particular feature in the input image. If the input image contains the feature that neuron is responsible for, that neuron's output will be especially large. For example:

{{< image src="digit-zero-top-left-feature.jpg" alt="A small 28 × 28 grayscale image with a single curved stroke in the top-left corner and the rest of the image blank." caption="The upper-left portion of the digit 0 [source: Neural Networks and Deep Learning]" >}}

If the 1st neuron in the hidden layer is responsible for detecting a feature like the one above, then when it computes the weighted sum over every input neuron, it will assign especially large weights to the input neurons in that upper-left region, and smaller weights to everything else. In other words, "being responsible for a feature" is, in practice, achieved entirely through how the weights are distributed.

By the same logic, the 3 features below are each handled by the hidden layer's 2nd, 3rd, and 4th neurons.

{{< image src="digit-zero-quadrant-features.jpg" alt="Three side-by-side 28 × 28 grayscale images, each keeping only one curved stroke, located at the upper-right, lower-left, and lower-right respectively." caption="From left to right: the upper-right, lower-left, and lower-right portions of the digit 0 [source: Neural Networks and Deep Learning]" >}}

Put these 4 features together, and they form a complete handwritten image of the digit 0!

{{< image src="handwritten-digit-zero.jpg" alt="A 28 × 28 grayscale handwritten image of the digit 0, formed by four curved strokes closing into a complete oval." caption="A handwritten image of the digit 0" >}}

So when we feed this handwritten "0" image into the neural network, the first 4 neurons in the hidden layer each detect the feature they're responsible for, and each produces an especially large output. From there we can infer that the output layer's first neuron, when computing its weighted sum over every hidden-layer neuron, will necessarily assign large weights to those first 4 neurons — because it "knows" that those 4 features together are what signal the digit 0.

With that process in mind, we can go back to the earlier question (why the output layer has 10 neurons instead of 4) and find it much easier to picture. When the output layer has 10 neurons, each output neuron symbolizes a digit, and whether it fires (produces a large output value) depends directly on which shape features the hidden layer detected — the connection between the two is direct. But when the output layer only has 4 neurons, each output neuron instead symbolizes a single bit, and it becomes much harder to build a natural connection between "which shape features the hidden layer detected" and "what this particular bit should be."

## Conclusion

In this article we stepped into the neural network's own point of view and watched it take a 28 × 28 handwritten-digit image all the way from raw pixel values, through the shape features captured by the hidden layer, to a classification produced by the output layer — and along the way we explained why the output layer uses 10 neurons instead of 4.

Up to this point, though, we've assumed the neural network has "already finished training," with all its weights conveniently sitting in the right place. The next article, [Deep Learning Fundamentals: The MNIST Dataset and the Cost Function](../mnist-and-cost-function/), picks up from here and looks at how a neural network actually learns — that is, how it adjusts its own parameters (weights and biases) so its output keeps getting more accurate. The images and examples in this article all come from [Neural Networks and Deep Learning, Chapter 1](http://neuralnetworksanddeeplearning.com/chap1.html); read the original text there for the full derivation.

### References

- [Neural networks and deep learning](http://neuralnetworksanddeeplearning.com/chap1.html)
- [Why do we have to normalize the input for an artificial neural network? – Stack Overflow](https://stackoverflow.com/questions/4674623/why-do-we-have-to-normalize-the-input-for-an-artificial-neural-network)
