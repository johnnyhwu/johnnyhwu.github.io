---
# weight: 1
title: "AWS Lightsail WordPress 教學：如何綁定你的專屬網域 (以 Namecheap 為例)"
date: 2023-08-03
lastmod: 2025-09-20
draft: false
description: "想為您架設在 AWS Lightsail 上的 WordPress 網站綁定自訂網域嗎？本篇完整教學將帶您一步步完成 Namecheap 設定、Lightsail DNS 配置與 WordPress 更新，讓您的網站告別 IP 位址，立即提升專業形象。"
featuredImage: "featured-image.png"

tags: ["SSL", "AWS", "Namecheap", "WordPress"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

本文為 Lightsail x WordPress 系列的第三篇文章！在第一篇文章中（[如何透過 AWS Lightsail 與 WordPress 建立自己的網站](../aws-lightsail-wordpress/)），我們介紹如何在 AWS Lightsail 服務中租用自己的 Server，並在 Server 上建立一個 WordPress 網站。

接著，在第二篇文章（[Lightsail x WordPress：WordPress 網站的備份與回復](../wordpress-backup-and-restore/)）中，我們分享了如何安全且有效的備份與回復自己的網站，也提到在回復網站時你可能會遇到的坑！ 在本篇文章中，我們將介紹如何將既有的網域（Domain）綁定到自己的 WordPress 網站上！

網域就像是一個網站的招牌，如果你想好好經營自己的部落格或是賣場，那一定得將網域綁定到自己的網站上，否則其他人就只能透過 **Server 的 Public IP** 來存取你的網站：Ｄ

## 在 Namecheap 中申請網域

如果你還沒購買一個網域，那我推薦使用 [Namecheap](https://www.namecheap.com/) 購買！當然市面上有許多網域的提供商，可以再爬爬文選擇自己最喜歡的，本文將以 Namecheap 舉例說明。如何在 Namecheap 上購買網域，網路上已經有許多相關的教學文章，這裡就不再贅述～

## 在 AWS Lightsail 中設定 DNS Record

在 Namecheap 上購買好自己的 Domain 之後，我們要在 [AWS Lightsail](https://aws.amazon.com/tw/lightsail/) 中進行一些設定，讓使用者在瀏覽器輸入這個 Domain 時，可以被導引至我們的網站上。 首先，點擊 Lightsail 側邊欄的「Domains & DNS」選單：

{{< image src="lightsail-dns-setting.png" alt="Lightsail 儀表板，左側邊欄選取 Domains & DNS 項目，右側顯示 Create a DNS Zone 面板與 Create DNS zone 按鈕" caption="在 Lightsail 的側邊欄點擊 Domain & DNS" >}}

接著點擊「Create DNS Zone」，將自己的 Domain Name 填寫上去。在 Domain Source 的地方，如果你的 Domain 是在 AWS Route 53 服務上取得的，那你應該選擇第一項：

{{< image src="lightsail-domain.png" alt="Lightsail 的 Domain configuration 畫面，網域來源選擇使用其他註冊商註冊的網域，並有一個輸入已註冊網域名稱的文字欄位" caption="建立 DNS Zone，並輸入自己的 Domain" >}}

建立好 DNS Zone 後，點擊 Assignment Tab，並點擊「Add Assignments」：

{{< image src="lightsail-domain-assign.png" alt="Lightsail DNS zone 頁面選取 Assignments 分頁，顯示 Domain assignments 區塊與 Add assignment 連結" caption="選擇 Assignment Tab" >}}

將你的 Domain Assign 到自己的 Static IP 上（如果你不知道如何在 Lightsail 中為 Server 設定 Static IP，可以參考[本文](../aws-lightsail-wordpress/)最後的補充處）：

{{< image src="lightsail-static-ip.png" alt="Lightsail 的 Add assignment 表單，選擇網域名稱、Ubuntu-Wordpress-IP 資源與 Static IP address 選項，Result 一行確認該網域將解析到此執行個體" caption="將目前的 Domain Assign 到 Server 的 Static IP" >}}

完成 Domain 的 Assignment 後，來到 DNS records 的 Tab，你可以看到有一筆新的 A Record 被新增上去了。這個 A Record 紀錄的是你的 Domain 應該被導引到哪一個 Public IP：

{{< image src="lightsail-dns-setting-2.png" alt="Lightsail 的 DNS records 分頁，A records 區段顯示一筆新增的 A 記錄，將記錄名稱對應到目標 IP" caption="在 DNS records Tab 中可以看到一個 A Record 被新增上去" >}}

## 在 Namecheap 中設定 Name Servers

在 Lightsail 中完成設定之後，AWS 的 Domain Name System 已經建立了 Domain 所對應到的 Server 的相關資訊。接著，我們還需要在購買 Domain 的機構（本文為 Namecheap）中進行一些設定！

首先，回到 Lightsail 的 Domains Tab 頁面，注意到頁面下方記載了 AWS 的 Domain Name Server 的位置：

{{< image src="lightsail-nameerver.png" alt="Lightsail DNS zone 的 Domains 分頁，以紅框標出 Name servers 區段，列出四個 AWS name server：ns-1371.awsdns-43.org、ns-1551.awsdns-01.co.uk、ns-781.awsdns-33.net 與 ns-462.awsdns-57.com" caption="回到 Domain Tab 注意 Name Serves 的部分" >}}

接著，在 Namecheap 的左側欄選單中選擇 Domain List，並點擊你的 Domain 旁邊的 MANAGE：

{{< image src="namecheap-domain-list.png" alt="Namecheap 的 Domain List 頁面，左側邊欄選取 Domain List，右側顯示一列狀態為 Active 的網域與 Manage 按鈕" caption="進到 Namecheap 並點擊側邊欄的 Domain List 並點擊 Domain 旁邊的 Manage" >}}

在設定 Name Servers 的地方選擇 Custom DNS，並且把剛剛出現在 Lightsail 中 AWS 的四個 Name Servers 位置貼過來：

{{< image src="namecheap-settings.png" alt="Namecheap 網域管理頁面，Nameservers 選項設為 Custom DNS，並將來自 Lightsail 的四個 AWS name server 逐行填入" caption="將 Lightsail 中的四條 Name Servers 位置一一貼到 Custom DNS 中" >}}

填寫完 Custom DNS 的資訊後，記得要按下右上角的綠勾勾，才真的有把你填寫的資訊儲存下來！

## 在 DNS Checker 中查看 Propagation 狀況

完成上述三個步驟之後，所有的設定基本上已經完成。接著就是等待 DNS Record 被傳播到全球的 DNS Server 中！可以在 [DNS Checker](https://dnschecker.org/) 中輸入你的 Domain，就可以查看這個 Domain 相關的 DNS Records 已經被傳播到全球的哪些 DNS Servers 上了！等待一段時間之後，就可以看到分布在全球的部分 DNS Servers 都有我們的 DNS Records：

{{< image src="dns-checker.png" alt="DNSChecker.org 的 DNS Propagation Map 世界地圖，多個伺服器位置皆顯示綠色勾號，代表 DNS 記錄已在幾乎所有地區完成解析" caption="透過 DNS Checker 查看 DNS Record 的傳播狀況" >}}

這邊再簡單介紹一下 DNS Records 的概念：DNS Records 有很多不同的種類，其實就是在用各種不同的方式來描述一個 Domain 對應到什麼東西。

以我們在 Step 2 中對 Lightsail 的設定，主要就是新增了一個 A Records（其中一種 DNS Records），A Records 述說這個 Domain 會對應到哪一個 Server（Public IP）。

一旦我們的 DNS Records 在全球的 DNS Servers 被記錄下來，當今天在世界某個角落的使用者，在瀏覽器中輸入我們的 Domain 後並按下 Enter 後，瀏覽器就可以向鄰近的 DNS Servers 詢問這個 Domain 到底指向哪一台 Server，瀏覽器就可以向正確的 Server（也就是實際擁有我們的 WordPress 網站的 Server）發出請求，瀏覽我們的 WordPress 網站。

## 在 WordPress 中設定 Domain

當我們的 Domain 的 DNS Records 完成傳播之後，我們就可以在瀏覽器中輸入 Domain，理論上就可以成功存取到自己的 WordPress 網站。 但這時候你可能會發現，當網站完整呈現在瀏覽器後，上頭的 URL 會從原來網站的 Domain 變成 Server 的 Public IP。主要是因為我們的 WordPress 後臺沒有進行相對應的調整：

{{< image src="wordpress-domain-setting.png" alt="WordPress 一般設定頁面，WordPress 位址與網站位址欄位皆設為新的 http 網域，網站介面語言設為繁體中文" caption="在 WordPress 後台將「WordPress 位址」與「網站位址」改為正確的 Domain" >}}

如上圖所示，我們需要在 WordPress 後台將「WordPress 位址」與「網站位址」改為正確的 Domain：「http://your_domain」。

## 結語

在本篇文章中，我們透過 5 個步驟（在 Namecheap 中申請網域、在 AWS Lightsail 中設定 DNS Record、在 Namecheap 中設定 Name Servers、在 DNS Checker 中查看 Propagation 狀況、在 WordPress 中設定 Domain）介紹如何取得一個 Domain，並將該 Domain 指向網站的 Server（也就是指向 WordPress 網站），讓訪客都可以夠過你的 Domain 來存取你的網站！
