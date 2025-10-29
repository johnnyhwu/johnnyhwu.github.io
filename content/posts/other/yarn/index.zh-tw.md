---
# weight: 1
title: "比 NPM 更好用？新一代 Node.js 套件管理工具 Yarn 入門教學"
date: 2023-06-07
lastmod: 2025-10-30
draft: false
description: "還在使用 NPM 嗎？來試試更高效的 Node.js 套件管理工具 Yarn！本篇新手教學將帶您從安裝開始，一步步了解 Yarn 的基本用法與核心概念，輕鬆提升您的專案管理與開發效率。"
featuredImage: "featured-image.png"

tags: []
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

如果你對 [Node.js](https://nodejs.org/en) 略知一二的話，大概會知道它的套件管理工具 [NPM](https://www.npmjs.com/)。然而，今天的主角不是他 ~ 今天要介紹的是 [Yarn](https://yarnpkg.com/) —— 另外一個更優質的套件管理工具。

Yarn 的出現是為了改善 NPM 中的一些問題，包含速度、安全性等等。此外，Yarn 的用法也和 NPM 大同小異，讓開發者可以輕鬆地適應這款新的套件管理工具！ 今天這篇文章不會深入的介紹 Yarn，而是想要讓從來沒聽過 Yarn 的開發者，對其有一個清楚又簡單的第一印象！

## 從安裝 Node.js 開始！

想要使用 Yarn，必須確保你的電腦上已經安裝了 Node.js，可以透過以下指令查看你的 Node.js 版本：

```bash
node -v
```

如果出現一個版本號（例如：v12.22.9）表示你已經有安裝過了，如果出現的是「Command not found」之類的文字，表示你需要先安裝 Node.js。因為網路上已經有非常多的安裝教學，這裡就不再贅述！

## 透過 Node.js 安裝 Yarn

有了 Node.js 後，我們就可以透過 NPM 來安裝 Yarn！我們通常會先在本機上以 Global 的方式安裝 Yarn 套件，接著再透過「yarn command」在專案資料夾中安裝特定的 (Local) Yarn 版本。這樣可以確保所有人在這個專案的資料夾底下，都會是使用相同的 Yarn 版本。 執行以下指令以 Global 方式安裝 Yarn：

```bash
sudo npm install -g yarn
```

接著執行：

```bash
yarn --version
```

如果出現類似版本好的資訊「1.22.19」就表示安裝成功囉！

## 在專案資料夾中安裝特定版本的 Yarn

接著，我們要在專案資料夾中安裝特定版本的 Yarn。我們首先建立一個資料夾：

```bash
mkdir my_project
cd my_project
```

接著，執行以下指令來安裝 Berry 版本的 Yarn：

```bash
yarn set version berry
```

這個步驟會在專案資料夾底下建立「.yarn/releases/」與「.yarnrc.yml」來儲存目前 Local 版本的 Yarn 的資訊。 我們可以再一次顯示目前的 Yarn 版本：

```bash
yarn --version
```

得到「3.6.0」可以發現與剛剛的不同！

## Global Yarn vs Local Yarn

實際上，如果我們再 cd 出目前的專案資料夾，再顯示一次 Yarn 版本時，此時顯示的會是 Global Yarn 的版本。因為每次當我們在執行 yarn command 時，Yarn 就會在目前的目錄底下找找看有沒有 **.yarnrc.yml** 的存在，.yarnrc.yml 這個檔案會存一個 Yarn 的路徑。如果 .yarnrc.yml 存在時，yarn command 執行時就會交由 .yarnrc.yml 所記錄的 Local Yarn 執行；反之，如果 .yarnrc.yml 不存在時，yarn command 執行時就會交由 Global Yarn 執行。

## 基本 yarn command

對於 Yarn 有了基本的理解後，接著就是記得以下最基本的 yarn command！ 透過以下指令來初始化專案資料夾，此時「package.json」會被建立，此檔案用來記錄這個專案的基本資訊，以及所有使用到的套件。此外，「lock.json」還會被建立用來鎖定所有套件的固定版本。

```bash
yarn init
```

Yarn 中 package.json 與 yarn.lock 的關係，就像是 NPM 中 package.json 與 package-lock.json 的關係。如果你不知道 yarn.lock 或是 package-lock.json 是什麼，可以參考此篇[文章](https://ithelp.ithome.com.tw/articles/10191888)！ 此外，當你想要在目前的專案中安裝 package.json 中提到的所有套件，可以執行：

```bash
yarn install
```

也可以透過：

```bash
yarn add package-name
```

來下載並安裝某一個套件，並且更新到 package.json 與 yarn.lock 中！

## 結論

在本篇文章中，你對於 Yarn 這個 Node.js 的套件管理工具有了一個初步的認識，如果你想更深入的學習其他 yarn command 可以參考 [Yarn 官方文件](https://yarnpkg.com/cli/install)。最後，補充道如果你在你的專案中使用 Yarn 要記得[撰寫正確的「.gitignore」檔案](https://yarnpkg.com/getting-started/qa#which-files-should-be-gitignored)，確保重要的 Yarn 資訊有被 Git 記錄下來！
