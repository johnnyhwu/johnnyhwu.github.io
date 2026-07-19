---
# weight: 1
title: "告別制式主機！AWS Lightsail WordPress 架站教學：從零開始掌握完整控制權"
date: 2023-08-01
lastmod: 2025-09-20
draft: false
description: "想擺脫套裝服務的限制，完全掌控自己的網站嗎？本篇 AWS Lightsail 教學將帶您一步步建立專屬伺服器，從零開始安裝 Nginx、MySQL 並架設 WordPress，打造一個高彈性、高自由度的網站。"
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

在 2023 年，想要建立一個網站來經營自己的部落格或是網路賣場可以說是相當容易，點擊幾個按鈕，一個 WordPress 網站就誕生了！然而，這種點擊幾個按鈕就建立一個 WordPress 網站的服務通常都沒什麼彈性。

舉例來說，他不會讓你 SSH 到伺服器上去修改 WordPress 的 Code，更不會讓你直接把 MySQL 的資料全部 Dump 出來做備份，許許多多的操作都必須額外在 WordPress 上安裝套件來完成。

因此，如果想要建立自己的網站，還是建議租用一台伺服器，試著自己在上頭安裝 Web Server 與 WordPress 來建立自己的網站！

今天這篇文章就是想和大家分享如何透過 AWS 的 Lightsail 服務與 WordPress，簡單幾個步驟就建立自己的網站。不過還是要提醒讀者，這種建立網站方法需要自己處理資安上的防護，如果對此完全沒有概念的話，可能要斟酌是否採用此方法！

## 成功註冊 AWS 帳號並且進入 Lightsail 服務

在開始建立網站之前，你需要先擁有一個 AWS 帳號。註冊 AWS 帳號的流程非常簡單，這邊就不再贅述！註冊完成後，找到 Lightsail 服務並點擊他，你會來到下方的頁面：

{{< image src="aws-lightsail.png" alt="瀏覽器中的 Amazon Lightsail 首頁，顯示 Good evening 問候語、目前尚無任何執行個體的訊息，以及橘色的 Create instance 按鈕" caption="進入 AWS 的 Lightsail 服務" >}}

## 透過 Lightsail 建立一台 Instance

接著，我們要透過 Lightsail 服務向 AWS 租用一台 Instance。可以簡單想成就是租用一台電腦，我們的網站將會部署在這台電腦上。點擊目前右面中的「Create Instance」後，會來到 Instance 的設定頁面。 首先是選擇 Instance 要放在地球上的哪一個位置：

{{< image src="lightsail-zone.png" alt="Lightsail 的 Select your instance location 畫面，區域選項網格中 Tokyo ap-northeast-1 被標示選取，下方的 Availability Zone 選擇 Zone A" caption="選擇 Instance 的 Availability Zone 與 Region" >}}

在 AWS 中 Availability Zone 與 Region 是兩個重要的觀念，一個 Region 裡頭會包含多個 Availability Zone，可以參考此[文件](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/RegionsAndAZs.html)來更深入的理解，這邊就不詳細的介紹！

你的 Instance 的位置距離你的目標客群愈近，他們在瀏覽網站所需要的延遲時間通常也會愈短。因為我的網站的目標客群主要是亞洲人，我就把 Instance 放在 Tokyo。

接著，要選擇 Instance Image，也就是你希望這個 Instance 要使用什麼作業系統，甚至是需要再多安裝什麼軟體：

{{< image src="lightsail-image.png" alt="Lightsail 的 Pick your instance image 畫面，平台選擇 Linux/Unix，blueprint 選擇 Ubuntu 22.04 LTS" caption="選擇 Lightsail Instance Image" >}}

這邊我只想要在 Instance 上安裝一個乾淨的 Ubuntu 22.04 作業系統即可！在下方的「Optional」欄位則不需要特別填寫。 接著，需要選擇 Instance 的硬體規格。這邊就比較因人而異了，因為我只想要單純建立一個自己的部落格，瞬間流量應該不至於太高，租用每個月 5 鎂或 10 鎂的規格就相當夠用：

{{< image src="lightsail-spec.png" alt="Lightsail 的 Choose your instance plan 畫面，顯示每月 3.5 至 40 美元的方案，其中選取 10 美元方案 (2 GB RAM、2 vCPUs、60 GB SSD)" caption="選擇 Lightsail Instance 硬體規格" >}}

最後則是需要給你的 Instance 一個名稱，因為這台 Instance 是要來建立 WordPress 網站，因此我給他取了個名字：

{{< image src="instance-name.png" alt="Lightsail 的 Identify your instance 畫面，執行個體命名為 Ubuntu-Wordpress，數量為 1" caption="幫你的 Instance 取個名字吧" >}}

上述的設定都完成之後，就點擊最後的「Create Instance」囉！如果你看到以下畫面，就代表你成功的在 Lightsail 上建立一台 Instance 囉！

{{< image src="lightsail-instance.png" alt="Lightsail 儀表板卡片，顯示 Ubuntu-Wordpress 執行個體具有 2 GB RAM、2 vCPUs、60 GB SSD，位於 Tokyo Zone A 且狀態為 Running" caption="成功在 Lightsail 上建立一台 Instance" >}}

## 安裝 Web Server (Nginx)

恭喜你完成前面兩個步驟，距離終點已經相當接近了！在第三個步驟中，我們需要在剛剛建立好的 Instance 中安裝 Web Server，這裡會選擇 Nginx。

首先，點擊剛剛建立的 Instance，並透過 SSH 連線到 Instance 上：

{{< image src="connect-to-instance.png" alt="Ubuntu-Wordpress 執行個體詳細頁面的 Connect 分頁，提供瀏覽器版 SSH 用戶端的 Connect using SSH 按鈕" caption="連線到 Instance 上" >}}

如果你出現以下畫面，代表你成功的透過 SSH 連線到 Instance 上了！接下來，你想對這台 Instance 做任何事情都可以：Ｄ

{{< image src="ssh-connection.png" alt="終端機顯示成功以 SSH 登入 Ubuntu 22.04.1 LTS，列出系統負載、記憶體與磁碟使用量等系統資訊，最後停在 ubuntu 的命令提示字元" caption="成功透過 SSH 連線到 Instance 上" >}}

接著，執行以下指令來啟動 Ubuntu 上的 Firewall，並且允許 SSH 的連線：

```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

查看目前 Firewall 的狀態：

```bash
sudo ufw status
```

接著在 Instance 上安裝 Web Server (Nginx)：

```bash
sudo apt update
sudo apt install nginx
```

安裝完之後，記得要在 Firewall 上設定，允許 HTTP 與 HTTPS 流量：

```bash
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
```

此時，在瀏覽器的網址列輸入你的 Instance 的 Public IP 如果出現以下頁面就表示 Web Server 建立成功囉：

{{< image src="nginx-welcome.png" alt="瀏覽器顯示 Nginx 預設的 Welcome to nginx! 頁面，確認 Web 伺服器已成功安裝並運作" caption="在瀏覽器輸入 Public IP 可以存取到 Nginx 的 Welcome 頁面" >}}

## 安裝 Database Management System (MySQL)

有了 Web Server 就可以處理來自世界各地的 Request，讓大家可以透過 HTTP/HTTPS 來存取到你的網站。接著，我們還需要安裝 DBMS。透過 DBMS 來管理 Database，而在 Database 中儲存你的 WordPress 文章、頁面等資訊。這邊的 DBMS 選擇 MySQL。

執行以下指令來安裝 MySQL：

```bash
sudo apt install mysql-server
```

安裝完成之後，進入到 MySQL 介面：

```bash
sudo mysql
```

輸入以下 SQL 指令來更改 Root User 的密碼：（要記得把 SetRootPasswordHere 換成你的密碼）

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql\_native\_password BY 'SetRootPasswordHere';
```

如果出現「Query OK」，代表這個 SQL Statement 被成功的執行！ 離開 MySQL：

```sql
exit;
```

接著進入到 MySQL 的安全設定介面：

```sql
sudo mysql\_secure\_installation
```

接著需要回答以下問題：

1.  Enter password for user root：輸入剛剛我們替 Root User 設定的密碼。
2.  Would you like to setup VALIDATE PASSWORD component?：輸入 y
3.  Please enter 0 = LOW, 1 = MEDIUM and 2 = STRONG：輸入 2
4.  接著我的畫面出現 Estimated strength of the password: 100：表示剛剛我替 Root User 設定的密碼的強度
5.  Remove anonymous users?：輸入 y
6.  Disallow root login remotely?：輸入 y
7.  Remove test database and access to it?：輸入 y
8.  Reload privilege tables now?：輸入 y

## 在 MySQL 中建立 WordPress 專屬的 Database

有了 MySQL 後，我們需要在裡頭替等等要建立的 WordPress 網站建立一個專屬的 Database。未來 WordPRess 網站的一些資訊就會存放在這個 Database 裏頭。 進入 MySQL：（輸入剛剛替 Root User 設定的密碼）

```bash
sudo mysql -p
```

建立 Wordress Database：

```sql
CREATE DATABASE wordpress DEFAULT CHARACTER SET utf8 COLLATE utf8\_unicode\_ci;
```

接著也在 MySQL 中建立一個 User，以及這個 User 的密碼：（your\_strong\_password 要替換成你的密碼）

```sql
CREATE USER 'wordpress-user'@'localhost' IDENTIFIED BY 'your\_strong\_password';
```

如果想要查看 MySQL 中所有 User：

```sql
SELECT user FROM mysql.user;
```

如果剛剛在建立 User 時出現：

```text
ERROR 1819 (HY000): Your password does not satisfy the current policy requirements
```

表示這個 User 的密碼強度不夠！可以輸入以下指令來了解密碼的 Requirement：

```sql
SHOW VARIABLES LIKE 'validate\_password%';
```

建立好 User 之後，賦予這個 User 擁有所有權限來操作 WordPress Database：

```sql
GRANT ALL PRIVILEGES ON \`wordpress\`.\* TO "wordpress-user"@"localhost";
```

離開 MySQL：

```sql
FLUSH PRIVILEGES;
exit;
```

## 安裝 PHP

走到這裡，我們已經安裝好 Nginx (Web Server) 和 MySQL (DBMS)，最後還需要安裝 PHP！主要是因為 WordPress 這支大程式主要就是透過 PHP 寫成的，如果要讓 WordPress 執行起來，這台電腦上就必須可以執行 PHP 的程式碼。 安裝 PHP 以及相關套件：

```bash
sudo apt install php-curl php-gd php-intl php-mbstring php-soap php-xml php-xmlrpc php-zip php-fpm php-mysql php-bcmath php-imagick
```

接著，需要 Restart PHP-FPM Process，因此先查看目前安裝的 PHP 版本：

```bash
php -v
```

我目前 PHP 的版本是 8.1.2，因此：

```bash
sudo systemctl restart php8.1-fpm
```

## 設定 Nginx

雖然已經有了 Web Server，但是我們還沒對它做任何設定，甚至沒告訴它網站資料夾會在哪一個位置，因此當使用者向它發出 Request 時，他始終只會顯示預設的 Welcome 頁面。 首先，新增一個檔案到指定路徑，並用 nano 編輯器開啟它：

```bash
sudo nano /etc/nginx/sites-available/wordpress
```

並將以下內容複製到檔案中（需要特別注意 PHP FPM 的版本有沒有正確）：

```bash
server {
        listen 80;
        root /var/www/wordpress;
        index index.php index.html index.htm index.nginx-debian.html;
        # server\_name myexampleblog.com www.myexampleblog.com;

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

為了要讓 Nginx 啟動上述的 Server 內容，需要將這個 Configuration 檔案建立一個 Soft Link 到「sites-enabled」目錄底下：

```bash
sudo ln -s /etc/nginx/sites-available/wordpress /etc/nginx/sites-enabled/
```

並將「sites-enabled」目錄底下預設的 Configuration 檔案移除：

```bash
sudo unlink /etc/nginx/sites-enabled/default
```

最後，確定目前的 Nginx 設定有沒有錯誤：

```bash
sudo nginx -t
```

## 下載 WordPress

切換到 tmp 目錄，並且下載最新版本的 WordPress：

```bash
cd /tmp
curl -LO https://wordpress.org/latest.tar.gz
tar xzvf latest.tar.gz
```

將解壓縮後得到的 WordPress 目錄複製到我們在上一個步驟中在 Nginx Configuration 中設定的網站根目錄：

```bash
sudo cp -a /tmp/wordpress/. /var/www/wordpress
```

此外，記得還要將這個根目錄的 User 和 Group 設定為 www-data：

```bash
sudo chown -R www-data:www-data /var/www/wordpress
```

接著再複製一份新的 wp-config.php，然後修改裡面的內容：

```bash
sudo cp /var/www/wordpress/wp-config-sample.php /var/www/wordpress/wp-config.php
sudo nano /var/www/wordpress/wp-config.php
```

請參考[這個網站](https://api.wordpress.org/secret-key/1.1/salt/)將下方的 Phrase 填入：

```php
define( 'AUTH\_KEY',         'put your unique phrase here' );
define( 'SECURE\_AUTH\_KEY',  'put your unique phrase here' );
define( 'LOGGED\_IN\_KEY',    'put your unique phrase here' );
define( 'NONCE\_KEY',        'put your unique phrase here' );
define( 'AUTH\_SALT',        'put your unique phrase here' );
define( 'SECURE\_AUTH\_SALT', 'put your unique phrase here' );
define( 'LOGGED\_IN\_SALT',   'put your unique phrase here' );
define( 'NONCE\_SALT',       'put your unique phrase here' );
```

此外，為了讓 WordPress 能夠成功的連線到 Database，需要將下方 Database 的資訊輸入：

```php
define( 'DB\_NAME', 'database\_name\_here' );
define( 'DB\_USER', 'username\_here' );
define( 'DB\_PASSWORD', 'password\_here' );
```

最後，記得將這份檔案儲存後關閉～

## WordPress 網站設定

恭喜你來到了最後一個步驟！ 重新啟動 Nginx：

```bash
sudo systemctl restart nginx
```

在瀏覽器中輸入 Instance 的 Public IP，如果看到以下頁面表示 Nginx 已經成功的執行 WordPress 這支程式：

{{< image src="install-wordpress.png" alt="WordPress 安裝精靈的第一個畫面，顯示 WordPress 標誌與語言選擇清單，English (United States) 被標示選取，並有 Continue 按鈕" caption="安裝 WordPress" >}}

接下來，就按照 WordPress 的安裝程序，你的 WordPress 網站就誕生囉！

## 補充

剛剛前面我們都是透過 Chrome 來 SSH 到 Instance，但是我自己比較喜歡從我自己 Mac 的 Terminal SSH 到 Instance 上，不喜歡還要開啟 Chrome、登入 AWS、進到 Lightsail 才能連線到我的 Instance（實在是太麻煩了），因此這邊補充怎麼做到這件事情。

首先，來到 Networking 的 Tab 之下，並在「Public IP」的地方點擊「Attach Static IP」：

{{< image src="set-static-ip.png" alt="Lightsail 的 Networking 分頁顯示 IPv4 networking，包含 public 與 private IP 欄位以及 Attach static IP 連結" caption="替你的 Instance 設定 Static IP" >}}

並且給你的這組 Static IP 取一個名字然後把他 Attach 到目前這台 Instance 上：

{{< image src="static-ip-name.png" alt="Lightsail 的 Create and attach a static IP 對話框，靜態 IP 命名為 Ubuntu-Wordpress-IP，並有 Create and attach 按鈕" caption="給你的 Static IP 取一個名字吧" >}}

這樣做的目的是為了避免 Instancce 如果重新開機後，換成另外一組 Public IP。

完成之後，再回到「Connect」的 Tab，並點擊最下方的「Download default key」：

{{< image src="ssh-key.png" alt="Lightsail 的 Connect 分頁顯示 Use your own SSH client 區塊，使用者名稱為 ubuntu，並有 Download default key 連結" caption="下載 Instance 的 Default Key" >}}

在自己的本機上，將透過上圖提供的 Username、Public IP 與 SSH Key 連線到這台 Instance 上。在你的本機端將剛剛下載下來的 pem file 權限修改成 400：

```bash
chmod 400 LightsailDefaultKey-ap-northeast-1.pem
```

最後就可以透過 SSH 連線到自己的 Instance 囉：

```bash
ssh -i LightsailDefaultKey-ap-northeast-1.pem ubuntu@PUBLIC\_IP
```

## 結語

在本篇文章中我們使用 AWS 的 [Lightsail](https://aws.amazon.com/tw/lightsail/) 服務取得一台自己的 Server/Instance，並在自己的 Instance 上安裝 Nginx (Web Server)、MySQL (DBMS) 以及 WordPress，成功建立自己的 WordPress 網站！

透過這種方式建立網站，大大提升我們對網站的掌控度，我們可以針對 Server 做更有彈性的設定（EX. Firewall），也可以針對 WordPress 的 Source Code 進行一些客製化的修改！

最棒的是，我們可以不需要仰賴 WordPress 的 Plugin 就幫自己的網站做最全面的備份！ 在 [Lightsail x WordPress：WordPress 網站的備份與回復](../wordpress-backup-and-restore/)一文中，將會介紹如何針對自己的網站做備份與回復！
