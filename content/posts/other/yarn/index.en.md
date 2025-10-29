---
# weight: 1
title: "A Beginner's Guide to Yarn: The Fast and Secure Alternative to NPM"
date: 2023-06-07
lastmod: 2025-10-30
draft: false
description: "Looking for a faster, more secure alternative to NPM? This beginner's guide introduces Yarn, the modern Node.js package manager. Learn how to install Yarn, set up project-specific versions, and use essential commands to streamline your development workflow."
featuredImage: "featured-image.png"

tags: []
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

If you're somewhat familiar with [Node.js](https://nodejs.org/en), you've likely heard of its package manager, [NPM](https://www.npmjs.com/). However, NPM isn't the star of our show today. We're here to introduce [Yarn](https://yarnpkg.com/)—another, more advanced package manager.

Yarn was created to address some of NPM's shortcomings, including issues with speed and security. Furthermore, Yarn's commands are very similar to NPM's, making it easy for developers to switch over to this new tool. This article won't dive deep into Yarn's advanced features; instead, it aims to give developers who have never heard of Yarn a clear and simple first impression.

## Start with Installing Node.js!

To use Yarn, you must have Node.js installed on your computer. You can check your Node.js version with the following command:

```bash
node -v
```

If a version number appears (e.g., v12.22.9), it means you already have it installed. If you see a message like "Command not found," you need to install Node.js first. There are many great installation tutorials online, so we won't cover that process here.

## Installing Yarn via Node.js

Once you have Node.js, you can use NPM to install Yarn! Typically, you'll first install the Yarn package globally on your machine. Then, you can use the `yarn` command to set up a specific (local) Yarn version within your project directory. This ensures that everyone working on the project uses the exact same version of Yarn.

Execute the following command to install Yarn globally:

```bash
sudo npm install -g yarn
```

Next, run:

```bash
yarn --version
```

If you see a version number like "1.22.19," the installation was successful!

## Installing a Specific Yarn Version in a Project Directory

Next, let's install a specific version of Yarn within a project directory. First, create a new directory:

```bash
mkdir my_project
cd my_project
```

Then, run the following command to set the Yarn version to Berry (the modern version of Yarn):

```bash
yarn set version berry
```

This step creates a `.yarn/releases/` directory and a `.yarnrc.yml` file in your project folder. These files store the information for the local version of Yarn.

We can check the Yarn version again:

```bash
yarn --version
```

You should now see something like "3.6.0," which is different from the global version we saw earlier!

## Global Yarn vs. Local Yarn

If you `cd` out of the current project directory and check the Yarn version again, it will display the global Yarn version. This is because every time you run a `yarn` command, Yarn checks the current directory for a **.yarnrc.yml** file. This file contains the path to a specific Yarn executable. If `.yarnrc.yml` exists, the command will be executed by the local Yarn version specified in that file. If it doesn't exist, the command falls back to the globally installed Yarn.

## Basic Yarn Commands

Now that you have a basic understanding of Yarn, here are the essential commands to remember.

To initialize a project directory, use the following command. This will create a `package.json` file, which records basic project information and all its package dependencies. It also creates a `yarn.lock` file to lock the specific versions of all packages.

```bash
yarn init
```

The relationship between `package.json` and `yarn.lock` in Yarn is just like the relationship between `package.json` and `package-lock.json` in NPM. If you're not familiar with `yarn.lock` or `package-lock.json`, you can learn more from this [article](https://ithelp.ithome.com.tw/articles/10191888) (content in Chinese).

Additionally, when you want to install all the packages listed in `package.json` for the current project, you can run:

```bash
yarn install
```

You can also use:

```bash
yarn add package-name
```

This command downloads and installs a specific package, updating both `package.json` and `yarn.lock` in the process.

## Conclusion

In this article, you've gained a preliminary understanding of Yarn, the package manager for Node.js. If you want to dive deeper and learn more commands, check out the [official Yarn documentation](https://yarnpkg.com/cli/install). Finally, one last tip: if you use Yarn in your project, remember to [configure your `.gitignore` file correctly](https://yarnpkg.com/getting-started/qa#which-files-should-be-gitignored) to ensure that essential Yarn files are properly tracked by Git.
