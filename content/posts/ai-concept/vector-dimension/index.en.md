---
# weight: 1
title: "Is a Vector 1D or 5D? The Two Meanings of Dimension"
date: 2026-06-23
lastmod: 2026-06-23
draft: false
description: "A vector is called 1-dimensional, yet [1, 2, 3, 4, 5] is also a 5-dimensional vector. Dimension has two distinct meanings, and this post untangles both."
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

Read enough linear algebra or deep learning material and you'll quickly run into a standard line: a scalar is 0-dimensional, a vector is 1-dimensional, a matrix is 2-dimensional, and anything past 3 dimensions is just called a tensor. (Scalars, vectors, and matrices can technically all be viewed as tensors too — they just happen to have fewer axes.)

Then, a few pages later in the same book, you'll see a vector like `[1, 2, 3, 4, 5]` — five numbers — described as "a 5-dimensional vector."

So which is it — 1-dimensional or 5-dimensional? This article first lays out how scalars, vectors, matrices, and tensors relate to one another, and then comes back to answer that question. The short version: "dimension" doesn't mean the same thing in those two sentences at all.

## Scalars, Vectors, Matrices, and Tensors

To answer the question above, we first need to put all four terms in the same framework. TensorFlow's framing is the most direct: they're all tensors, and the only difference between them is how many "axes" each one has.

{{< image src="scalar-vector-matrix.jpg" alt="A side-by-side comparison of a Scalar, a Vector, and a Matrix, shown as a single value, a row of values, and a 2D table respectively, each labeled with its shape." caption="Scalar, Vector, and Matrix compared [source: TensorFlow]" >}}

- A **scalar** is a single value. Its shape has no elements at all — no axes — so it's called a rank-0 tensor.
- A **vector** is a list of values. Its shape has one element, meaning it has one axis, making it a rank-1 tensor.
- A **matrix** is made of elements arranged along two axes, so its shape has two elements, making it a rank-2 tensor.

"Axis" sounds abstract, but there's an easy way to think about it: how many indices does it take to pull a single number out of the structure? A scalar needs none, a vector needs one (`v[2]`), and a matrix needs two (`m[1][2]`). The number of indices is exactly the rank.

Once you keep adding axes past that point, there stop being separate names for each case.

{{< image src="tensor.png" alt="A diagram of a tensor with three axes, where the values are stacked as cubes, and the shape is made up of three elements." caption="A tensor with three or more axes [source: TensorFlow]" >}}

Once the axis count reaches 3 or more, we just call it a tensor — its shape now has 3 elements, so it can also be called a rank-3 tensor. This shape shows up constantly in practice — an RGB image, for instance, is exactly this: three axes for height, width, and channel.

## Dimension: Axis Count, or Element Count?

So when we say a scalar is 0-dimensional, a vector is 1-dimensional, and a matrix is 2-dimensional, "dimension" here means the number of axes.

But once we zoom in on vectors specifically, the meaning shifts. Describing a vector's "dimension" is really describing how many dimensions the vector space it lives in has — in other words, how many elements the vector contains. For example:

- [1, 2, 3] lives in a 3-dimensional vector space
- [-1, -5, 4, 5, 8] lives in a 5-dimensional vector space
- [0, 0, 0, 0, 0, 0, 0] lives in a 7-dimensional vector space

A more concrete, real-world example is the [MNIST handwritten digit images](../mnist-and-cost-function/): a 28 × 28 image, once flattened, becomes a vector with 784 elements — so it lives in a 784-dimensional vector space, commonly called a "784-dimensional vector." Its corresponding label, in turn, is a 10-dimensional vector.

Which means **"dimension" has two distinct meanings**:

- A vector's **element count** (representing which vector space that vector lives in)
- A tensor's **axis count** (representing that tensor's rank)

Back to the question we opened with: it's correct to call `[1, 2, 3, 4, 5]` either 1-dimensional or 5-dimensional, because the two claims are counting different things. It has exactly one axis, so it's a rank-1, 1-dimensional tensor; at the same time, it has 5 elements and sits in a 5-dimensional vector space, so it's also a 5-dimensional vector.

In practice, the context tells you which one is meant: is the discussion about the data's "shape" or its "content"? In frameworks like NumPy and PyTorch, "dimension" usually means the shape/rank kind (e.g. `ndim`); in a linear algebra context, it usually means the dimensionality of a vector space.

## Conclusion

What separates scalars, vectors, matrices, and tensors really just comes down to how many axes each one has. "Dimension," meanwhile, points at one of two different things depending on context: a tensor's axis count (its rank), or how many elements a vector contains (i.e., the dimensionality of the vector space it lives in). Next time you see "a 1-dimensional vector" and "a 5-dimensional vector" mentioned in the same breath, just check whether the person is counting axes or counting elements, and most of the confusion clears up.

### References

- [matrices – why do people say "x dimensional vector" when vectors have only one dimension? – Mathematics Stack Exchange](https://math.stackexchange.com/questions/2152360/why-do-people-say-x-dimensional-vector-when-vectors-have-only-one-dimension)
- [Introduction to Tensors | TensorFlow Core](https://www.tensorflow.org/guide/tensor)
- [PyTorch Deep Learning, Taught by a Core Developer (book, Chinese)](https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=9135738)
