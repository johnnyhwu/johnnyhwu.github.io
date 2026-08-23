---
# weight: 1
title: "What Is Heroku, and How Is It Different From AWS?"
date: 2023-02-08
lastmod: 2023-02-08
draft: false
description: "Heroku looks like the fast way to ship an app, but it actually runs on top of AWS. This post explains Heroku, Dynos, and why teams choose a PaaS over AWS directly."
featuredImage: "featured-image.jpg"

tags: ["AWS", "Heroku"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

Once you've finished writing an application locally, the next step is usually letting other people actually use it — which means deploying it to a server. That's exactly where the headaches start: should you maintain the server hardware yourself? How do you handle network security? How do you protect your users' data?

While googling those questions, you'll probably run into Heroku. It looks like it can get your application online quickly while sparing you all that maintenance work. This post explains three things in plain terms: what Heroku is, what a Dyno is, and — since your app ends up running on AWS anyway — why not just use AWS directly.

## What Is Heroku

[Heroku](https://dashboard.heroku.com/login) is a platform that lets you deploy applications quickly. The word "platform" should sound familiar: [Medium](https://medium.com/) is a platform for articles — you publish what you write, and others can read it; [Shopee](https://shopee.tw/) is a platform for shopping — you list a product, and others can buy it.

Heroku plays the same role. Once you've put in the hard work to build a piece of software and want everyone to be able to use it, you can put it on Heroku. From then on, people can access your service the same way they browse any website — just type a URL into their browser.

## What Is a Dyno

On your own computer, you double-click an application icon and the program opens. How fast it launches, how efficiently it runs, and how smooth it feels all depend heavily on your computer's performance. If your machine is an old relic, using it is never a pleasant experience.

The same logic applies to running your application in the cloud: Heroku also needs to provision a "computer" for it — just a virtual one, which Heroku calls a **Dyno**. Think of a Dyno as a virtual machine that supplies the compute resources your application needs to run.

As your user base grows and the application starts to lag, you have two levers to pull: upgrade the specs of each Dyno, or spin up more Dynos to share the load. Heroku's billing is based on exactly that — how many Dynos you use, and for how long. (Back in 2022, Heroku still had a free Dyno tier; that free tier was discontinued later that same year, so running any application today requires a paid plan.)

Here's a fact many people don't realize: we assume we're deploying our application "on Heroku," but under the hood, the code actually runs on [AWS (Amazon Web Services)](https://aws.amazon.com/) machines.

## Why Not Just Use AWS Directly

Since the application ends up running on AWS anyway, why not skip Heroku entirely and use AWS from the start?

To answer that, we first need to understand what AWS is. AWS is an "Infrastructure as a Service" (IaaS) provider. Providers like this buy up huge plots of land around the world and build "data centers" — and a data center is exactly what we mean when we say "the cloud." When you upload a file to Google Drive, what actually happens is that your data gets stored in one of Google's data centers.

Thanks to these IaaS providers, we no longer need to buy our own hard drives or run our own server rooms just to store files — "uploading to the cloud" takes care of it.

The catch is that providers like AWS, Google Cloud, and Azure focus their business on managing the underlying hardware reliably, not on making life comfortable for developers. As a result, developers who want to use these IaaS platforms "directly" usually have to climb a steep learning curve first: how to slice up a VPC, how to configure IAM permissions, which EC2 instance type to pick — just standing up a service securely is already a substantial amount of homework.

{{< image src="aws-certificate.jpg" alt="Overview diagram of AWS's official certification system, listing certification names across various tiers and specialty areas" caption="AWS's certification offerings [source: AWS]" >}}

The diagram above makes the point clearly: AWS alone offers a whole lineup of certifications and courses just for its own services. It's easy to see how much time it can take to actually get good at using them.

Heroku's role is to act as the bridge between developers and IaaS. When we deploy an application to Heroku (which you now know really means deploying to AWS), we can manage it through a relatively simple CLI and a clearly designed dashboard, instead of dealing directly with that entire layer of underlying infrastructure configuration.

{{< image src="heroku-dashboard.jpg" alt="Screenshot of Heroku's web dashboard showing an application's management options" caption="Heroku Dashboard [source: Heroku]" >}}

In other words, Heroku is a platform built by engineers who are experts in AWS, for other engineers. Because it's a layer built on top of AWS (an IaaS), we call Heroku a "Platform as a Service" (PaaS) provider.

## Conclusion

The value Heroku (PaaS) offers is shielding us from the complexity of operating AWS (IaaS) directly, which makes deploying an application simpler and faster. The trade-off is flexibility and price: there's less room to tune the underlying specs, and it costs more than running your own EC2 instances. For a project that's still validating an idea and doesn't want to get bogged down by infrastructure, that trade-off is usually worth it.

Now that you understand Heroku, the natural next read in this series is [Deploying a Django Project to Heroku on an M1 Mac](../deploy-django-on-heroku-macos/), which walks through actually shipping a Django project.
