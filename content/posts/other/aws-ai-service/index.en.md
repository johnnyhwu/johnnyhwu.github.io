---
# weight: 1
title: "AWS AI Services Explained: 13 Ready-to-Use ML Capabilities"
date: 2023-02-10
lastmod: 2023-02-10
draft: false
description: "AWS's machine learning lineup can be overwhelming. This guide covers the top AI Services layer -- 13 use cases, from medical transcription to fraud detection, you can call as an API without training a model."
featuredImage: "featured-image.jpeg"

tags: ["AWS", "Machine Learning"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

AWS, short for Amazon Web Services, is Amazon's cloud computing platform, offering everything from compute and storage to machine learning. The machine learning corner of AWS in particular has so many tools that it can feel overwhelming the first time you look.

{{< image src="machine-learning-on-aws.jpeg" alt="Diagram of AWS's machine learning product categories, arranged from top to bottom in five layers." caption="AWS's machine learning products roughly fall into 5 layers [source: AWS Machine Learning Foundation Course on Udacity]" >}}

As the diagram above shows, AWS's machine learning products roughly fall into five layers: AI Services, ML Services, ML Infrastructure, Frameworks, and Getting Started. Moving from top to bottom, each layer is less abstract and requires more hands-on work from you. The topmost layer, AI Services, is a set of ready-made services you can call through an API; the further down you go, the closer you get to training your own model and managing your own compute resources.

This article focuses on the top layer, AI Services -- what application areas it covers, and what the flagship service in each area actually does.

## AWS AI Services

{{< image src="aws-ai-services-overview.jpeg" alt="Overview diagram of AWS AI Services' 13 use-case categories and their flagship services." caption="An overview of AWS's AI Services [source: AWS Machine Learning Foundation Course on Udacity]" >}}

As shown above, AWS's AI Services are organized into 13 use-case categories. Their biggest value proposition: developers don't need to walk through the "five steps of machine learning" ([defining the problem](../define-problem/), [building a dataset](../prepare-dataset/), [training a model](../model-training/), [evaluating the model](../model-evaluate/), and [running inference](../model-inference/)) themselves -- they can plug AI capability directly into their own applications. AWS has already trained the model; all you have to do is prepare the input and consume the output.

Put plainly, this layer is for the case where "someone else has already solved my problem." If what you need is speech-to-text, face detection, or product recommendations -- generic tasks like these -- training a model from scratch is usually not worth it. Conversely, if your problem is tightly coupled to your own business data, that's when you need to move down to the ML Services layer instead.

Let's go through all 13 categories in order.

### HEALTH AI

If you've ever seen a doctor, this scene probably looks familiar: the doctor asks questions while typing away at the keyboard the whole time. Doctors have to type up their diagnosis as text to use as the basis for prescriptions, which splits their attention between the patient and the keyboard. [Amazon Transcribe Medical](https://aws.amazon.com/transcribe/medical/) exists to solve exactly this -- it uses speech recognition to turn the conversation between doctor and patient into text, eliminating manual note-taking and letting the doctor focus back on the patient.

### INDUSTRIAL AI

On the factory floor, [Amazon Monitron](https://aws.amazon.com/monitron/) combines sensors with a data analytics platform to predict when a machine is about to fail. Being able to predict a machine's crash time ahead of schedule means maintenance can be scheduled proactively, avoiding the losses from an entire production line grinding to a halt.

### ANOMALY DETECTION

This category is exactly what it sounds like: detecting anomalies. [Amazon Lookout for Metrics](https://aws.amazon.com/lookout-for-metrics/) can be used to catch anomalies in business data, such as a sudden drop in sales or a sudden dip in customer satisfaction.

### CHATBOT

[Amazon Lex](https://aws.amazon.com/lex/) lets you quickly add a chatbot into your application.

### PERSONALIZATION

For personalized recommendations, [Amazon Personalize](https://aws.amazon.com/personalize/) lets developers build their own recommendation systems, commonly used in retail, entertainment, and media platforms.

### FORECASTING

[Amazon Forecast](https://aws.amazon.com/forecast/) provides time-series forecasting to help businesses predict future changes in their data, such as next quarter's sales or product demand.

### FRAUD

[Amazon Fraud Detector](https://aws.amazon.com/fraud-detector/) is used to detect online fraud. Online fraud takes many forms, and account registration and online payments are both common targets.

### CODE DEVELOPMENT

[Amazon CodeGuru](https://aws.amazon.com/codeguru/) helps developers improve code quality and identifies so-called "expensive" code -- the sections that are dragging down performance.

### VISION

On the vision side, [Amazon Rekognition](https://aws.amazon.com/rekognition/) can quickly locate faces in photos and videos.

### SPEECH

[Amazon Polly](https://aws.amazon.com/polly/) turns text into realistic-sounding speech.

### TEXT

[Amazon Textract](https://aws.amazon.com/textract/) extracts text from photos and scanned documents. Compared to typical OCR, Textract's edge is that it understands table structure, so it can pull out the relationships between the data in a table as well.

### CONTACT CENTER

[Contact Lens](https://aws.amazon.com/connect/contact-lens/) analyzes the conversation between a customer service agent and a customer, reads the sentiment and issue from the conversation, and files the conversation into categories afterward.

### SEARCH

[Amazon Kendra](https://aws.amazon.com/kendra/) is an intelligent search service that helps users quickly find answers across an entire website.

Thirteen categories in one sitting is a lot to remember, so here's a quick-reference table:

| Category | Flagship service | In one line |
|---|---|---|
| HEALTH AI | Amazon Transcribe Medical | Medical conversation to text |
| INDUSTRIAL AI | Amazon Monitron | Predictive machine failure |
| ANOMALY DETECTION | Amazon Lookout for Metrics | Business data anomaly detection |
| CHATBOT | Amazon Lex | Chatbots |
| PERSONALIZATION | Amazon Personalize | Personalized recommendation systems |
| FORECASTING | Amazon Forecast | Time-series forecasting |
| FRAUD | Amazon Fraud Detector | Online fraud detection |
| CODE DEVELOPMENT | Amazon CodeGuru | Code quality and performance review |
| VISION | Amazon Rekognition | Face detection in images and video |
| SPEECH | Amazon Polly | Text-to-speech |
| TEXT | Amazon Textract | Document text and table extraction |
| CONTACT CENTER | Contact Lens | Contact center conversation analysis |
| SEARCH | Amazon Kendra | Intelligent search |

(This list reflects AWS's service lineup as of 2022; AWS updates its AI product line frequently, so it's worth double-checking the official docs before you actually use one of these.)

## Conclusion

This article covered AWS's AI Services, walking through the flagship service and typical use case for each of the 13 categories. The point of this layer is that you don't have to train your own model -- you consume general-purpose AI capability as an API instead. The next article moves one layer down to cover [AWS ML Services](../aws-ml-service/), where you handle your own data and models.
