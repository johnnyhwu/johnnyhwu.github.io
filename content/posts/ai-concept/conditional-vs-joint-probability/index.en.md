---
# weight: 1
title: "Conditional vs Joint Probability: A Deck of Cards Clears It Up"
date: 2022-05-14
lastmod: 2022-05-14
draft: false
description: "Conditional and joint probability confuse most beginners: similar notation, different questions. This guide compares them with a deck of cards, then covers AND and OR."
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

{{< image src="featured-image.jpg" alt="Featured image for the article on conditional vs. joint probability" caption="Featured image for this article [source: Pixabay]" >}}

In the previous article, [Probability From Zero: Marginal, Joint & Conditional](../basic-probability-joint-marginal-conditional/), we covered probability notation, random variables (RV), the three basic types of probability, and the multiplication rule. Of those three, conditional probability and joint probability are the pair beginners mix up most often: both talk about "two events," and their symbols even look a little alike — but they're actually asking completely different questions.

This article tackles exactly that confusion. We'll lay the two side by side using the same deck of playing cards, then go a step further and cover how AND and OR work in probability. By the end, the next time you run into \( P(A \mid B) \) and \( P(A \cap B) \), you should be able to tell at a glance what each one is really asking.

## Conditional Probability

Conditional probability is the probability of one event happening given the "premise" that another event has already happened. Suppose A and B are two different events; the probability of A happening given that B has happened is written \( P(A \mid B) \).

The subtlety here: once you fix a premise, the scope you're considering shrinks. Instead of looking at every possibility, you're now only looking at the slice where "B already holds."

With a deck of cards: let B = "drawing a red card" and A = "drawing a 4." Then \( P(A \mid B) = 2/26 \). Because the premise is "red," the scope has already shrunk from 52 cards down to the 26 red ones, and among those 26, there are 2 fours.

## Joint Probability

Joint probability is the probability of "two or more" events happening at the same time. If A and B are two different events, the probability of both happening at once is written \( P(A \cap B) \). The "\( \cap \)" symbol means "intersection" — in plain terms, both conditions have to hold.

Same deck of cards: suppose A = "drawing a 6" and B = "drawing a red card." Then \( P(A \cap B) = 2/52 \), because out of 52 cards, only 2 are both a 6 and red (the 6 of hearts and the 6 of diamonds).

Notice the denominator here is 52, not 26 — that's the key difference from conditional probability.

## Conditional vs. Joint Probability

For anyone new to probability, the two sections above can still feel pretty similar, so let's take the exact same question and ask it two different ways, side by side.

First phrasing: what's the probability of "drawing a red card that's also a 4"? That's a joint probability, written \( P(\text{Red and } 4) = P(\text{Red} \cap 4) \). Picture 52 cards face-down on a table — we don't know any card's color or number yet. But we do know that, out of those 52, 2 cards are both red and a 4. So \( P(\text{Red and } 4) = 2/52 \).

Second phrasing: what's the probability of "drawing a 4, given that we already know it's red"? That's a conditional probability, written \( P(4 \mid \text{Red}) \). Picture that before drawing, someone has already pulled out every red card and laid them out on the table — we can only draw from those 26. Among those 26 red cards, 2 are a 4, so \( P(4 \mid \text{Red}) = 2/26 = 1/13 \).

Here's the difference laid out as a table:

| | Joint probability \( P(\text{Red} \cap 4) \) | Conditional probability \( P(4 \mid \text{Red}) \) |
|---|---|---|
| What it asks | The probability of both events happening at once | The probability of one event, given that another already holds |
| Scope (denominator) | All 52 cards | Only the 26 red cards |
| Answer with cards | 2/52 | 2/26 = 1/13 |

In other words, a conditional probability's premise swaps out the denominator, while a joint probability is always computed over the full sample space.

These two numbers can actually check each other. Using the multiplication rule: for the joint probability \( P(\text{Red and } 4) \), \( P(\text{Red and } 4) = P(4 \text{ and Red}) \) equals \( P(4 \mid \text{Red}) \times P(\text{Red}) = 1/13 \times 1/2 = 1/26 = 2/52 \), matching the number we got by directly counting cards.

*Side note: \( P(\text{Red}) = 1/2 \), since half of a 52-card deck is red!*

## AND vs. OR

Now that the two definitions are clear, there's one more question that comes up constantly in practice: when you combine multiple events, how do you actually compute the probability? That's the difference between AND and OR.

### AND: Multiply the Probabilities

Joint probability is exactly the probability of two events happening "at the same time" — the AND case. Starting from the multiplication rule:

\( P(A \cap B) = P(A \mid B) \times P(B) \)

Let's use a more everyday example. Say you have two dice: event A = "the first die shows a 6," event B = "the second die shows a 1."

By the multiplication rule, we can compute \( P(A \mid B) \) and \( P(B) \) first, then get \( P(A \cap B) \). \( P(A \mid B) \) asks: "given that the second die shows a 1, what's the probability the first die shows a 6?" You don't even need to calculate it to know the answer — whatever the second die shows has nothing to do with the first die. In this case, we say events A and B are "independent."

When A and B are independent, A's probability isn't affected by B, so \( P(A \mid B) = P(A) \). Plugging that back into the multiplication rule:

\( P(A \cap B) = P(A) \times P(B) = 1/6 \times 1/6 = 1/36 \)

### OR: Add the Probabilities

AND multiplies the probabilities of each event; OR adds them. Mathematically:

\( P(A \cup B) = P(A) + P(B) - P(A \cap B) \)

Why subtract an extra term? Because when you compute \( P(A) + P(B) \), the part where A and B overlap (i.e., both happening at once) gets counted twice, so you need to subtract it back out once.

Reusing the dice example — event A = "the first die shows a 6," event B = "the second die shows a 1" — and we already found \( P(A \cap B) = 1/36 \), so:

\( P(A \cup B) = 1/6 + 1/6 - 1/36 = 11/36 \)

## Conclusion

This article laid out the difference between conditional probability and joint probability: it comes down to whether the "scope" you're considering has been narrowed by a premise. A conditional probability's denominator only covers the cases where the premise holds, while a joint probability is always computed over the full sample space. We also covered how AND multiplies probabilities and OR adds them — remembering to subtract the double-counted intersection for OR.

If you'd like to go deeper into probability, Professor 葉丙成's [頑想學概率](https://zh-tw.coursera.org/learn/prob1) course on Coursera is a solid next step.
