---
# weight: 1
title: "告別「不安全」警告：為 AWS Lightsail 上的 WordPress 網站安裝免費 Let's Encrypt SSL 憑證"
date: 2023-08-04
lastmod: 2025-09-20
draft: false
description: "您的 WordPress 網站還在顯示「不安全連線」嗎？本篇教學將引導您如何在 AWS Lightsail 上，透過 Nginx 與 Certbot 為您的網站安裝免費的 Let's Encrypt SSL 憑證，輕鬆升級至 HTTPS，提升網站安全性與使用者信任。"
featuredImage: "featured-image.png"

tags: ["SSL", "AWS", "Nginx", "WordPress"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

本篇文章為 Lightsail x WordPress 系列的第 4 篇文章，在前 3 篇文章我們依序介紹了如何[透過 AWS Lightsail 建立一個 wordPress 網站](../aws-lightsail-wordpress/)，[並且給予網站一個網域（Domain）](../wordpress-namecheap-domain/)，最後[學習將網站進行備份與回復](../wordpress-backup-and-restore/)！在今天的文章中，我們要學習如何透過 [Let's Encrypt](https://letsencrypt.org/) 服務，賦予網站一個 SSL 憑證，讓我們的網站可以使用 HTTPS 協定。

本篇文章的適用情況為：在瀏覽器輸入網站的 Domain 時可以成功的存取到目標網站，只不過目前在 URL 的地方仍是顯示「http://your-domain.com」。此外，你必須能夠透過 SSH 連線到網站的 Server，並能夠透過 sudo 來安裝一些套件。我們使用 Nginx 作為我們的 Web Server。

## 在 Ubuntu 上安裝 Nginx 的 Certbot

首先，在 Ubuntu 上安裝適用於 Nginx 的 Certbot，透過 Certbot 來替網站進行 SSL Certificate 的設定：

```bash
sudo add-apt-repository ppa:certbot/certbot
sudo apt install python3-certbot-nginx
```

## 確保 Firewall 允許 HTTPS 流量通過

這邊需要確保 **Ubuntu 以及 Lightsail** 上都允許 HTTPS 流量，使用者才能成功透過 HTTPS 協定來瀏覽我們的網站。 在 Ubuntu 上檢查目前 Firewall 設定：

```bash
sudo ufw status
```

確保允許 HTTPS 流量通過，如果沒有的話，可以新增：

```bash
sudo ufw allow 'Nginx Full'
```

在 Lightsail 中，Instance 的 Networking 設定新增 HTTPS Rule：（下方的 IPv6 也可以新增）

{{< image src="lightsail-https-rule.png" caption="在 Lightsail 中允許 HTTPS 流量" >}}

## 在 Nginx 中設定 Domain

透過 Nano 編輯器開啟 Nginx 中 WodPress 網站的 Configuration 檔案：

```bash
sudo nano /etc/nginx/sites-available/wordpress
```

並且在「server_name」的地方補上 Domain：（剩下的是[之前](../aws-lightsail-wordpress/)就已經寫上去的內容）

```bash
server {
        listen 80;
        root /var/www/wordpress;
        index index.php index.html index.htm index.nginx-debian.html;
        server\_name your-domain.com;      

        location / {
                try\_files $uri $uri/ /index.php$is\_args$args;
        }
        location = /favicon.ico { log\_not\_found off; access\_log off; }
        location = /robots.txt { log\_not\_found off; access\_log off; allow all; }
        location ~\* \\.(css|gif|ico|jpeg|jpg|js|png)$ {
                 expires max;
                 log\_not\_found off;
        }
        location ~ \\.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi\_pass unix:/var/run/php/php8.1-fpm.sock;
        }

        location ~ /\\.ht {
                deny all;
        }
}
```

## 透過 Certbot 設定 SSL Certificate

執行以下指令來透過 Certbot 設定 SSL Certificate：（記得換成自己的 Domain）

```bash
sudo certbot --nginx -d myexampleblog.com
```

如果你看到「Congratulation」的字眼，就代表你設定成功了！ 我們還希望這個 SSL Certificate 可以自動的更新：

```bash
sudo certbot renew --dry-run
```

同樣的，如果你看到「Congratulation」的字眼，就代表你設定成功了！ 如果你成功走到這裡，就代表你的網站已經設定好 SSL Certificate，使用者可以透過 HTTPS 協定來和你的 Server 溝通。

## 從 WordPress 後台將網站位置改成 HTTPS

然而，如果你嘗試在瀏覽器中輸入「https://your-domain.com」，會發現根本沒辦法存取到自己的網站。這是因為在 WordPress 後台的設定中，WordPress 位置和網站位置都還是停留在「http://your-domain.com」，因此我們需要到 WordPress 後台進行設定。

然而，當你試著要連線到自己的 WordPress 後台時（http://your-domain.com/wp-admin），你發現根本連不上去！！！

別急，這是因為在上一個步驟中，Certbot 在 Nginx 的 WordPress Configuration（`/etc/nginx/sites-available/wordpress`）檔案中多加了一些設定，強制將 HTTP 流量導向 HTTPS，而因為 WordPress 後台還沒完成設定導致我們又無法以 HTTPS 成功存取到網站。

解決這個問題的方法有兩種：

第一種是直接到 MySQL 中，將 WordPress Database 裡頭的「home」與「site_url」的值 由「**http**://your-domain.com」改成「**https**://your-domain.com」。（這邊可以參考 [WordPress 的備份與復原](../wordpress-backup-and-restore/)一文中的復原環節）

第二種方法是先將 Nginx Configuration 檔案中 HTTPS 相關的設定註解掉，如此一來我們就可以透過 HTTP 進入 WordPress 後台，然後將「WordPress 位置」與「網站位置」的值由「**http**://your-domain.com」改成「**https**://your-domain.com」。再回到 Nginx Configuration 檔案將剛剛著解掉的東西解除。

{{< image src="wordpress-domain.png" caption="第二種方法：在 WordPress 後台設定 HTTPS" >}}

## 結語

當你進到一個網站時，它顯示「HTTP 不安全連線」，你會不會覺得毛毛的，想必你一定想趕快離開這個網站。因此，替自己的網站設定 SSL 憑證，讓使用者可以透過 HTTPS 瀏覽自己的網站是相當重要的！在本篇文章我們透過簡單 5 個步驟介紹如何取得 SSL Certificate，讓網站的瀏覽從 HTTP 變成 HTTPS。
