---
# weight: 1
title: "WordPress 網站備份、還原與搬家完整教學 (含新主機 IP 修改)"
date: 2023-08-02
lastmod: 2025-09-20
draft: false
description: "擔心網站心血付之一炬？本篇 WordPress 備份教學將帶您一步步操作，使用 SSH 與 MySQL 指令完整備份網站檔案與資料庫。同時解決網站搬家、更換主機 IP 後的還原問題，完整保護您的網站內容。"
featuredImage: "featured-image.png"

tags: ["AWS", "Nginx", "WordPress"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

在[如何透過 AWS Lightsail 與 WordPress 建立自己的網站](../aws-lightsail-wordpress/)一文中，我們介紹了如何使用 AWS 的 [Lightsail](https://aws.amazon.com/tw/lightsail/) 服務取得一台自己的 Server/Instance，並在自己的 Instance 上安裝 Nginx (Web Server)、MySQL (DBMS) 以及 WordPress，成功建立自己的 WordPress 網站！

擁有了自己的網站後，「備份網站」可以說是非常重要的任務，你一定也不希望自己長年累月的心血付諸流水。因此，本篇文章將基於[前一篇文章](../aws-lightsail-wordpress/)所建立的 WordPress 網站教大家如何備份與回復自己的網站！實際上，只要你能夠 **SSH 到自己的 Server** 上，就適用本篇文章的教學!

## WordPress 網站備份

相較於網站回復，網站備份可以說是相當簡單！只需要對「網站根目錄」與「資料庫」進行備份即可。 首先，對網站根目錄備份就是指將 `/var/www/wordpress` 打包成一個 ZIP：

```bash
sudo apt install zip
zip -r wordpress.zip /var/www/wordpress/
```

接著針對 MySQL 中 WordPress 的 Database 做 Dump 的動作：

```bash
mysqldump -u wordpress-user -p --opt wordpress --no-tablespaces > wordpress.sql
```

經過上述兩個步驟之後，在你的目前目錄底下會有「wordpress.zip」與「wordpress.sql」，需要透過 SCP 將他們傳回去自己的電腦上：

```bash
scp -i \[path to pem file\] ubuntu@\[public IP\]:\[path to wordpress.sql\] .
scp -i \[path to pem file\] ubuntu@\[public IP\]:\[path to wordpress.zip\] .
```

## WordPress 網站回復

網站回復跟網站備份的流程基本上一樣，只不過把操作反過來而已！ 在 Ubuntu 上安裝 unzip 工具：

```bash
sudo apt install unzip
```

將剛剛取得的網站根目錄進行解壓縮，並且移動到正確的位置：

```bash
unzip wordpress.zip
sudo mv wordpress /var/www/
```

記得！除了將網站根目錄搬移到正確位置外，還需要修改這個根目錄的權限（我們在[前一篇文章](../aws-lightsail-wordpress/)中也有這個操作）：

```bash
sudo chown -R www-data:www-data /var/www/wordpress
```

完成網站根目錄的回復之後，接著要將 WordPress 的 Database 也進行回復。主要就是將 wordpress.sql 直接寫回去一個空的「wordpress」Database 中：

```bash
mysql -u wordpress-user -p wordpress < wordpress.sql
```

做到這裡你可以試著在瀏覽器中網址列的地方搜尋你的 Server 的 Public IP，如果成功出現你之前的網站，那就表示網站已經回復成功啦！但是事情往往沒有這麼單純，我們通常在做網站回復的工作時，很可能不是回復在原來的 Server 上。

換句話說，原來在做網站備份時是從 A Server 進行備份，但是在做網站回復時卻是回復到 B Server 上。因為 A Server 與 B Server 經常擁有不同的 IP，加上我們目前所擁有的備份資料（wordpress.sql）裡頭的文件都是指向原來的 Server IP，就會導致即使我們在 B Server 上進行網站回復後，仍然沒辦法正常的顯示我們的網站。

如果你也遇到相同的問題，就需要在進行完上述的操作後，再到 MySQL 中針對 WordPress 的 Database 進行一些修改！ 首先，進入到 MySQL 下 SQL 的介面：

```bash
sudo mysql -p
```

輸入 Root 的密碼。 接著選擇使用 WordPress 的 Database：

```bash
use wordpress;
```

查看目前從另外一台 Server 所備份下來的 WordPress 網站的 Domain 是指到哪裡：

```sql
SELECT \* FROM wp\_options WHERE option\_name = 'home' OR option\_name = 'siteurl';
```

如果呈現出來的 Domain 和目前這台 Server 的 Public IP 不同，那麼 WordPress 網站就無法正確地被顯示出來，因此我們需要將 Databse 中所有關於舊的 Domain 都改成新的 Domain：

```sql
UPDATE wp\_options SET option\_value = replace(option\_value, 'https://www.oldurl', 'https://www.newurl') WHERE option\_name = 'home' OR option\_name = 'siteurl';
UPDATE wp\_posts SET guid = replace(guid, 'https://www.oldurl','https://www.newurl');
UPDATE wp\_posts SET post\_content = replace(post\_content, 'https://www.oldurl', 'https://www.newurl');
UPDATE wp\_postmeta SET meta\_value = replace(meta\_value,'https://www.oldurl','https://www.newurl');
```

記得，上面所有 SQL 指令的「https://www.oldurl」就是要改成原來的 WordPress 網站的 Domain，而「https://www.newurl」要改成「http://目前這台 Server 的 Public IP」。 最後離開 MySQL：

```sql
exit;
```

重新啟動 MySQL 與 Nginx 服務：

```bash
sudo systemctl restart mysql
sudo systemctl restart nginx
```

## 結語

「備份網站」一向是非常重要的任務，過去就曾經在自己的部落格網站中寫了一堆文章，但是因為久久忘記繳租用 Server 的費用，最後整台 Server 被砍掉，過去的心血當然也就付諸流水。在本篇文章中，介紹如何對[既有的網站](../aws-lightsail-wordpress/)進行備份與回復，讓你再也不怕自己的心血不見！
