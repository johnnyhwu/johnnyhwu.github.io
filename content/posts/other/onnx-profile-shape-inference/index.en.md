---
# weight: 1
title: "Unlock Your ONNX Models: Advanced Shape Inference & Profiling with onnx-tool"
date: 2023-06-11
lastmod: 2025-10-16
draft: false
description: "Discover 'onnx-tool', a powerful utility for advanced ONNX model profiling and shape inference. Easily analyze parameters, MACs, and solve dynamic shape issues for better visualization with Netron."
featuredImage: "featured-image.png"

tags: ["ONNX"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

In this article, I want to introduce a handy ONNX tool that allows you to profile and perform shape inference on ONNX models in a simpler and more efficient way. But first, what is ONNX?!

Here's the introduction to ONNX from its [official website](https://onnx.ai/): "**ONNX** (Open Neural Network Exchange) is an open format built to represent machine learning models. ONNX defines a common set of operators - the building blocks of machine learning and deep learning models - and a common file format to enable AI developers to use models with a variety of frameworks, tools, runtimes, and compilers."

That's right! The biggest advantage of ONNX is its ability to facilitate the conversion of our neural networks between different frameworks. Many online tools for converting models between TensorFlow and PyTorch are also built on ONNX: they first convert the model from its original format to ONNX, and then to the target format.

## ONNX Visualization Tool: Netron

When talking about ONNX, we have to mention [Netron](https://github.com/lutzroeder/netron)! Netron is an open-source visualizer for neural networks. It can visualize models designed for many deep learning frameworks, including ONNX, TensorFlow Lite, Caffe, Keras, and more. However, support for the more familiar PyTorch and TensorFlow is still experimental.

From my own experience, I find that Netron has the best compatibility with ONNX and is least likely to throw errors. Therefore, whenever I want to visualize a neural network, I first convert it to the ONNX format and then use Netron to visualize it!

The image below shows the result of visualizing an ONNX file with Netron: (You can also open it via this [link](https://netron.app/?url=https://media.githubusercontent.com/media/onnx/models/main/vision/classification/squeezenet/model/squeezenet1.0-3.onnx))

{{< image src="onnx-example.png" alt="Netron visualization of an ONNX model graph, starting from a data_0 input of shape 1x3x224x224 and flowing through Conv, Relu, MaxPool and Concat nodes with their weight and bias shapes labeled" caption="Visualizing an ONNX model in Netron" >}}

## ONNX Profile & Shape Inference

The star of this article isn't Netron, but another fantastic ONNX tool I've found — [onnx-tool](https://github.com/ThanatosShinji/onnx-tool). That's right! Its name is as simple and unpretentious as it gets: just "onnx-tool".

Whenever I visualize an ONNX model with [Netron](https://github.com/lutzroeder/netron), I often wish it could display not only the input and output tensor shapes of the model but also the output shapes of all intermediate operations.

As shown in the image below:

{{< image src="onnx-example-2.png" alt="Side-by-side ONNX graphs of the same CNN; the left graph labels only the input 1x1x28x28 and final shapes, while the right graph labels the intermediate tensor shape on every edge between Conv, Relu, MaxPool, Flatten and Gemm nodes" caption="(Left) Displaying only the initial and final shapes; (Right) Displaying the shapes of all operations" >}}

To make Netron display all the shapes, you must ensure that the ONNX file contains the shape information for the output of every operation. To achieve this, we need to perform "Shape Inference" on the ONNX model. The official ONNX library provides a simple shape inference function. However, this method has some limitations: it cannot handle dynamically generated shapes, such as those from Reshape or Concat operations.

This is where the shape inference feature of [onnx-tool](https://github.com/ThanatosShinji/onnx-tool) comes in, as it can handle such cases! Besides shape inference, [onnx-tool](https://github.com/ThanatosShinji/onnx-tool) can also perform profiling:

{{< image src="onnx-profile.png" alt="Profiling table listing each ONNX node with its MACs, compute percent, memory, parameter count and input and output shapes, ending in a total of about 666 million MACs and 61 million parameters" caption="Profiling an ONNX model" >}}

Through its profiling feature, we can find out the number of parameters (Params), multiply-accumulate operations (MACs), and the input/output shapes for each operation or the entire model. In addition to shape inference and profiling, [onnx-tool](https://github.com/ThanatosShinji/onnx-tool) has many other useful features waiting for you to explore!

## Conclusion

In this article, we introduced a handy [ONNX tool](https://github.com/ThanatosShinji/onnx-tool) that simplifies shape inference and profiling for ONNX models. Using it in combination with [Netron](https://github.com/lutzroeder/netron) for visualization can give you a more comprehensive understanding of your model! If you've never heard of ONNX before, you can refer to this [article](https://ithelp.ithome.com.tw/articles/10210800) for a basic understanding.
