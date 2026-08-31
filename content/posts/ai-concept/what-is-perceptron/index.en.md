---
# weight: 1
title: "Before Deep Learning, Understand the Perceptron"
date: 2022-02-03
lastmod: 2026-08-31
draft: false
description: "The perceptron is the ancestor of the neural network. How it weighs inputs against a threshold, why that threshold became the bias, and why one perceptron is a NAND gate."
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

Ever since AlexNet won the [ILSVRC](https://www.image-net.org/challenges/LSVRC/) in 2012, deep learning has steadily become the dominant approach, and artificial neural networks have been put to work on problems that traditional algorithms could not handle — including computer vision and natural language processing.

Before diving into the core ideas of deep learning, though, it is worth spending a little time on the ancestor of the neural network: the perceptron. This article explains what a perceptron is, how to write down its mathematics, why a single perceptron is equivalent to a NAND gate, and why chaining several perceptrons together lets them express any computation at all. These concepts are the foundation for everything else you will learn about neural networks.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **What a perceptron is**: the "artificial neuron" Rosenblatt proposed in 1957 — it takes several binary inputs and produces one binary output.
- **How it works**: multiply each input by its corresponding weight and sum them; if the sum exceeds the threshold, output 1, otherwise output 0.
- **The simplified formula**: ∑wx becomes the dot product w ⋅ x, and the threshold moves to the left-hand side as the bias (b), which captures how easily this neuron fires.
- **Equivalent to a NAND gate**: a perceptron with weights of -2 and a bias of 3 has exactly the truth table of a NAND gate — and since NAND is a universal gate, a network of perceptrons can express any computation.
- **Learning is the real difference**: a learning algorithm lets a perceptron tune its own parameters, and that is why it is more than a NAND gate in disguise.
{{< /admonition >}}

## What is a perceptron

The perceptron is the "artificial neuron" that [Frank Rosenblatt](https://en.wikipedia.org/wiki/Frank_Rosenblatt) invented in 1957, based on the idea of a biological nerve cell. In essence it is a simple binary linear classifier.

One thing to be clear about up front: the neurons used in modern published neural network models are no longer perceptrons but something else, called the [sigmoid neuron](../sigmoid-neuron/). So why learn about the perceptron at all? Because the sigmoid neuron's principles grew almost directly out of the perceptron's. Get the perceptron straight first and the sigmoid neuron will feel entirely natural later.

{{< image src="perceptron.jpg" alt="A diagram of a perceptron, with three input arrows x1, x2 and x3 on the left pointing at a circular neuron in the middle, and one output arrow on the right." caption="A perceptron takes *several* binary values and produces *one* binary value" >}}

As the diagram shows, a perceptron can take several inputs and produce one value. Here x1, x2, x3 and the output are all *binary values* — their value is either 0 or 1.

Rosenblatt also proposed a very direct way to compute a perceptron's output: multiply each input x by its own corresponding parameter w, then add all those products together; if the sum is greater than some threshold, output 1, otherwise output 0. **w** and **threshold** are the parameters of this one perceptron.

Written out as mathematics it looks like this:

{{< image src="perceptron-formula.jpg" alt="The perceptron's mathematics written as an inequality: output 0 when the sum of the input-weight products is less than or equal to the threshold, and 1 when it is greater." caption="The perceptron's operation expressed mathematically [source: Neural Networks and Deep Learning]" >}}

## Understanding the perceptron through a simple example

The formula above is a little abstract; an everyday example makes it much easier to follow. Think of x1, x2 and x3 as different *factors*, and the output as the final *decision*.

Suppose friends invite you out this weekend and you are torn about whether to go, because you are still weighing up three things:

- Whether the weekend will be sunny (you hate the rain)
- Whether anyone of the opposite sex is coming along (you would like to meet new people)
- Whether you can get a lift in someone's car (you would rather not take the train)

Those three *factors* are the perceptron's x1, x2 and x3, and the final *decision* about whether to go is the output. If the weekend is sunny, x1 is 1; if it rains, x1 is 0. If someone of the opposite sex is coming, x2 is 1, otherwise 0. x3 works the same way.

Because you care about these three things to different degrees, x1, x2 and x3 map to different parameters w inside the perceptron. Suppose you care enormously about "is anyone of the opposite sex coming" — so much that as long as someone is, you will decide to go even if the weekend is guaranteed to pour with rain and there is guaranteed to be no lift. Then w2 will be noticeably larger than w1 and w3.

Ranking the three factors by how much they matter — "is anyone of the opposite sex coming" > "will it rain this weekend" = "can I get a lift" — the values of w might be w1 = 3, w2 = 6, w3 = 3.

Besides w, the perceptron also has the threshold parameter, which in this example we set to 5. That way, even if "it will rain this weekend" (x1 = 0) and "there is no lift available" (x3 = 0), as long as "someone of the opposite sex is coming" (x2 = 1) the sum of 6 still exceeds 5, and the final decision (output) is still 1. Conversely, if we set the threshold to something very large (say 100), then even with all three factors going your way the sum of 12 still cannot clear the bar, and you would end up deciding not to go.

The example shows the distinct role each of the perceptron's two parameters plays: adjusting w adjusts the weight of each input — how much each factor matters to you — while adjusting the threshold is like adjusting how much you want to make a positive decision at all, that is, how easily the output comes out as 1.

## Several perceptrons form a network

The complexity of problems a single perceptron can handle is really quite limited; after all, it only does one thing — sum the weighted inputs and compare against a threshold. To solve more complicated real-world problems, you have to connect many perceptrons together into a neural network.

{{< image src="perceptron-network.jpg" alt="A diagram of a neural network built from many circular neurons arranged in several layers, with arrows connecting every neuron in a layer to every neuron in the next." caption="Several perceptrons form a neural network [source: Neural Networks and Deep Learning]" >}}

The diagram above organises 8 perceptrons into a neural network. The first layer has 3 neurons, each of which multiplies the inputs by weights (w), sums them, and outputs 1 or 0 depending on whether the sum clears the threshold. In other words, that layer makes three different decisions in one go. The neurons in the next layer then make decisions based on the previous layer's outputs (its decisions), so the further back a layer sits, the more complex and abstract its decisions become. This is why, in practice, we often build neural networks with a great many layers when tackling hard problems.

You may find something odd here: didn't we say at the start that a perceptron has only one output? Why does each perceptron in the diagram have several output arrows? It does still have only one output — that single output is simply fed into several neurons in the next layer at once, which is why it is drawn as several arrows.

## Simplifying the perceptron's mathematics

The original formula is, frankly, long-winded, so in practice we make two small rewrites to shorten it.

First, **∑wx** is the sum of each input multiplied by its weight, which is exactly a [dot product](https://en.wikipedia.org/wiki/Dot_product) and can be written directly as **w ⋅ x**, where both w and x are vectors. Second, moving the threshold from the right-hand side of the inequality to the left gives **−threshold**, which is just as wordy, so we use **b** to stand for it.

{{< image src="perceptron-formula-1.jpg" alt="The simplified perceptron formula, deciding between an output of 0 and 1 based on whether the dot product of w and x plus b is greater than 0." caption="The perceptron's simplified formula [source: Neural Networks and Deep Learning]" >}}

In the world of deep learning, w is usually called the **weight** and b the **bias**, and both are parameters of the neural network model. The rest of the articles in this series will also use weight and bias to describe a neural network's parameters.

The idea of bias often feels a bit abstract, but it becomes easy once you remember what it started life as — the threshold. It represents how easily this neuron's output comes out as 1. Thought of biologically, the bias is how easy it is to *activate* this neuron. If some neuron's bias is a large positive number (say 100), then whatever the input x is, the final output is very likely to be 1 (the neuron fires); conversely, when the bias is a small negative number (say -1), the output is very likely to be 0.

## A perceptron is equivalent to a NAND gate

So far we have treated the perceptron as something that *makes decisions*, but it can equally be viewed directly as a *logical function*. The simplest logical functions are the [logic gates](https://en.wikipedia.org/wiki/Logic_gate) taught in a digital circuit design course — AND, OR, NOT and that family.

{{< image src="perceptron-as-nand-gate-2.jpg" alt="A perceptron taking two inputs x1 and x2, with a weight of -2 marked on both input connections and a bias of 3 marked inside the neuron." caption="A perceptron can also behave exactly like a NAND gate" >}}

As the diagram shows, this perceptron takes two inputs (x1 and x2), both input weights (w1 and w2) are -2, and the bias is 3. With input 00 (x1=0, x2=0), (0 × -2) + (0 × -2) + 3 = 3, so the output is 1; inputs 01 and 10 give 1 as well. But with input 11, (1 × -2) + (1 × -2) + 3 = -1, so the output becomes 0. Lay all four cases out and you will find its truth table is exactly that of a NAND gate.

Speaking of NAND gates, anyone who has taken a digital circuits course will immediately think: the NAND gate is a *universal gate*. That is, NAND gates alone are enough to build any logical function you want.

{{< image src="adder-using-nand-gate.jpeg" alt="A circuit diagram of an adder built from several interconnected NAND logic gates." caption="An adder built purely from NAND gates [source: Wikimedia Commons]" >}}

The diagram above is an adder (a half adder) built only from NAND gates. Since a perceptron can be used as a NAND gate, every NAND gate in that diagram can naturally be swapped out for a perceptron.

{{< image src="adder-using-perceptron.jpg" alt="A circuit diagram with the same structure as the previous adder, but with every NAND logic gate replaced by a perceptron symbol, the connections marked with a weight of -2 and a bias of 3." caption="Replacing every NAND gate in the adder with a perceptron [source: Neural Networks and Deep Learning]" >}}

After the substitution, the original circuit diagram has instantly become a neural network. Look closely and you will spot something strange: the leftmost neuron has two outputs feeding into the same neuron, which never came up when we introduced the perceptron. The fix is simple — merge those two inputs into one and change the weight from -2 to -4, and the behaviour of the whole neural network is completely unchanged.

{{< image src="adder-using-perceptron-1.jpg" alt="The perceptron version of the adder circuit, with the two connections of weight -2 merged into a single connection of weight -4." caption="Swapping \"two connections of -2\" for \"one connection of -4\" [source: Neural Networks and Deep Learning]" >}}

Beyond that, we usually also draw the neural network's leftmost inputs using the *perceptron symbol*:

{{< image src="input-layer.jpg" alt="The neural network diagram of the adder, with an extra leftmost layer of input nodes x1 and x2 drawn as perceptron symbols." caption="Drawing the neural network's leftmost inputs as perceptrons forms a layer [source: Neural Networks and Deep Learning]" >}}

Once the inputs (x1 and x2) are drawn as perceptrons too, the left-hand side looks like an extra layer, and that layer is usually called the *input layer*.

You may again find something odd: why do the perceptrons in the input layer have no inputs? To avoid that confusion, the better way to think about it is not to treat the neurons in the input layer as genuine perceptrons at all, but as a special kind of neuron that exists purely to represent the whole neural network's input.

## A perceptron can express any computation

Putting the last two pieces together: a perceptron is equivalent to a NAND gate, and a NAND gate is a universal gate that can express any computation — so a neural network built from perceptrons can likewise express any computation.

"A perceptron can express any computation" sounds impressive, and it means we can assemble extremely powerful computing devices from them. But looked at another way it is a little deflating, since such a perceptron is, bluntly, nothing more than a NAND gate in disguise.

Don't lose faith in perceptrons, neural networks or deep learning just yet, though. Later researchers added other elements to the perceptron, the most crucial of which is the [learning algorithm](../gradient-descent/). With a learning algorithm, a perceptron can tune its parameters (weight and bias) *by itself*.

That is where perceptrons and NAND gates genuinely part ways: we don't have to assemble perceptrons into a neural network by hand and then set every parameter inside it manually — instead we let the whole neural network work its own parameters into the right positions.

## References

- [Neural networks and deep learning](http://neuralnetworksanddeeplearning.com/chap1.html)
- [Perceptron – Wikipedia](https://en.wikipedia.org/wiki/Perceptron)
- [NAND and NOR Gate as Universal Gate – Digital Electronics](https://sites.google.com/site/tanglindigitalelectronics/home/nand-and-nor-gate-as-universal-gate)
- [Logic gate – Wikipedia](https://en.wikipedia.org/wiki/Logic_gate)

## Conclusion

This article introduced the basic concepts of the perceptron, including how it sums its weighted inputs and compares them against a threshold, and the simplified formula that results from rewriting that threshold as a bias. It then used the equivalence between the perceptron and the NAND gate to explain why a neural network of perceptrons is enough to express any computation. Finally it noted that the learning algorithm is what makes a perceptron more than a NAND gate in disguise — something that can learn on its own.

[The next article](../sigmoid-neuron/) introduces a neuron much closer to the one modern neural networks actually use: the sigmoid neuron.
