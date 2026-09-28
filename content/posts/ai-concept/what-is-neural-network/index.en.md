---
# weight: 1
title: "Deep Learning, Step One: Neural Network Terminology"
date: 2026-06-11
lastmod: 2026-06-11
draft: false
description: "Zooming out from a single sigmoid neuron to a full network: meet the input, hidden, and output layers, and see why feedforward and recurrent networks differ in one thing."
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

In the [previous article on the sigmoid neuron](../sigmoid-neuron/), we focused on a single neuron: how it compares to a [perceptron](../what-is-perceptron/), and the sigmoid function's most important property, "smoothness." It's precisely because the output changes smoothly that an artificial neural network can adjust its parameters bit by bit and get closer and closer to the right answer.

This article pulls the camera back a level. Instead of looking at a single artificial neuron, we look at the whole neural network: what parts it's made of, how the input and output layers should be designed, and what actually separates a feedforward architecture from a recurrent one. These terms are the shared vocabulary for everything that follows in deep learning — get them straight now and no model architecture diagram will trip you up later.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Three basic components**: a row of neurons connected left to right — the leftmost column is the input layer, the rightmost is the output layer, and everything in between is collectively called the hidden layer.
- **"Hidden" isn't mysterious**: the name just means "neither input nor output," nothing more.
- **Deep neural network**: stacking many hidden layers builds a "deep" network — that's where the name deep learning comes from.
- **Designing the input/output layers**: this is almost entirely decided by the problem itself, e.g. a 28 × 28 grayscale image maps to 784 input neurons.
- **Feedforward vs. recurrent**: the only real difference is whether a feedback loop exists that lets information flow backward.
{{< /admonition >}}

## The Basic Building Blocks of a Neural Network

{{< image src="neural-network-basic.jpg" alt="A diagram of a three-layer neural network: neurons in an input layer on the left, one hidden layer in the middle, and an output layer on the right, connected layer to layer." caption="A 3-layer neural network [source: Neural Networks and Deep Learning]" >}}

A basic neural network looks roughly like the diagram above: rows of circles (neurons), connected left to right with lines.

By convention, the leftmost inputs are also drawn as circles so they look like neurons — these are called input neurons, and they naturally form a layer: the **input layer**. The rightmost layer is called the **output layer**, and its neurons are output neurons. Everything sandwiched in between is collectively called the **hidden layer**.

"Hidden layer" sounds a bit mysterious, but it really isn't. The name is only trying to say one thing: this layer is neither input nor output, and that's it.

The network in the diagram above has exactly one input layer, one hidden layer, and one output layer. Most modern neural networks stack many hidden layers on top of each other, forming a very "deep" network — which is exactly where the name **deep neural network** comes from. The whole process of a deep neural network repeatedly adjusting its internal parameters via a learning algorithm and gradually producing correct output is what we call **deep learning**.

{{< image src="neural-network-two-hidden-layers.jpg" alt="Another neural network diagram made of one input layer, two hidden layers, and one output layer, with neurons in adjacent layers fully connected." caption="The basic components of a neural network: input layer, output layer, and hidden layer [source: Neural Networks and Deep Learning]" >}}

The diagram above is another example, this time with two hidden layers.

One term worth flagging here: a neural network built by stacking many layers like this is often called a **multilayer perceptron**, or MLP for short. But as the previous article on the sigmoid neuron already pointed out, the neurons in a modern neural network are usually not perceptrons at all. To avoid confusion, this series consistently calls it a neural network and avoids the term "multilayer perceptron."

## Designing the Input and Output Layers

Compared to the hidden layer, designing the input and output layers is much more straightforward, because they're almost entirely dictated by the problem itself. Take a classic task as an example: handwritten-digit image classification. You feed in a photo of a handwritten digit, and the network has to output which digit, 0 through 9, that photo represents.

The most intuitive and common way to build the input layer is to treat every pixel's value in the image as one input neuron. Take a 28 × 28 grayscale image: "grayscale" means the image is made of a single channel, unlike an ordinary color image, which is made of three channels — red, green, and blue. So the whole image has 28 × 28 = 784 values in total, each representing the information at one position in the image. Assign one neuron to each value, and you get an input layer with 784 neurons.

The output layer depends on what you want the network to answer. Here the answer is a digit from 0 to 9, so each digit gets its own output neuron, for 10 in total. When the network believes the image is an "8," the output neuron representing "8" should output a value greater than 0.5. That gives an output layer with 10 neurons.

Designing the hidden layer, on the other hand, is far more complicated. How many layers to stack, and how many neurons to put in each one, is often a mix of the author's own ideas and technique — even a bit of an "art" — and it's hard to reduce to a handful of rules. Later articles in this series will cover some common design approaches.

## Feedforward and Recurrent Neural Networks

Every neural network discussed so far — whether built from perceptrons or sigmoid neurons — shares one property: the output of one layer becomes the input to the next, and information only ever moves forward, never back. This kind of network is called a **feedforward neural network**.

Put another way: suppose there's a sigmoid neuron (A) inside a feedforward neural network. Because there's no "feedback loop" anywhere in the network, whatever A computes at this instant only gets sent to the next layer — it never loops back to A itself.

Another kind of neural network deliberately includes a feedback loop, letting information also flow backward (toward the input layer). This is called a **recurrent neural network**. Suppose again there's a sigmoid neuron (A) inside one: A's output at this instant gets sent backward, and at the next instant, it becomes part of A's input again, alongside whatever new input arrives. The result is that A's output at the next instant is influenced by its own output from the instant before.

The difference between the two is summarized below:

| | Feedforward Neural Network | Recurrent Neural Network |
|---|---|---|
| Has a feedback loop? | No | Yes |
| Direction information flows | Forward only (input → output) | Forward, but can also flow backward |
| This instant's output | Depends only on this instant's input | Also depends on the previous instant's output |

## References

- [Neural networks and deep learning](http://neuralnetworksanddeeplearning.com/chap1.html)
- [Multilayer perceptron – Wikipedia](https://en.wikipedia.org/wiki/Multilayer_perceptron)
- [Feed Forward Neural Network Definition | DeepAI](https://deepai.org/machine-learning-glossary-and-terms/feed-forward-neural-network)
- [Feedforward neural network – Wikipedia](https://en.wikipedia.org/wiki/Feedforward_neural_network)

## Conclusion

This article pulled the camera back from a single artificial neuron to a whole neural network: we met the input layer, hidden layer, and output layer as the three basic components, saw how the input and output layers are designed around the problem itself, and worked out that the key difference between feedforward and recurrent neural networks comes down to whether a feedback loop exists.

[The next article](../handwritten-digit-classification/) stays at the whole-neural-network level and walks through how a complete neural network actually solves the "handwritten-digit image classification" problem.
