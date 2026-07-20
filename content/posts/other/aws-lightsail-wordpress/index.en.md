---
# weight: 1
title: "Build a WordPress Site on AWS Lightsail: The Complete Guide From Scratch"
date: 2023-08-01
lastmod: 2025-09-20
draft: false
description: "Learn how to build a flexible, self-hosted WordPress website on AWS Lightsail. This step-by-step guide walks you through installing Nginx, MySQL, and PHP on Ubuntu for complete control over your blog or business site."
featuredImage: "featured-image.png"

tags: ["SSL", "AWS", "Nginx", "WordPress"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

In 2023, creating a website to run your own blog or online store is remarkably easy. With just a few clicks, a WordPress site can be brought to life! However, these one-click WordPress creation services often lack flexibility.

For instance, they typically don't allow you to SSH into the server to modify the WordPress code, nor do they let you directly dump the entire MySQL database for backup. Many operations require installing additional plugins within WordPress.

Therefore, if you want full control over your website, it's recommended to rent a server and try installing a web server and WordPress yourself.

This article will guide you through creating your own website in just a few simple steps using AWS Lightsail and WordPress. A word of caution: this method requires you to handle your own security. If you are completely new to web security, you might want to consider if this approach is right for you.

## Register an AWS Account and Access Lightsail

Before you begin, you'll need an AWS account. The registration process is straightforward, so we won't cover it here. Once registered, find and click on the Lightsail service. You will be taken to the following page:

{{< image src="aws-lightsail.png" alt="Amazon Lightsail home page in a browser showing a Good evening greeting, a message that there are no instances yet, and an orange Create instance button" caption="Accessing the AWS Lightsail service" >}}

## Create an Instance with Lightsail

Next, we'll use Lightsail to rent an "Instance" from AWS. You can think of this as renting a computer where your website will be deployed. Click on "Create Instance" on the current page to go to the instance setup screen.

First, choose the physical location for your instance:

{{< image src="lightsail-zone.png" alt="Lightsail Select your instance location screen with a grid of region options where Tokyo ap-northeast-1 is highlighted, and Availability Zone A selected below" caption="Choosing the Instance's Availability Zone and Region" >}}

In AWS, "Region" and "Availability Zone" are two important concepts. A Region contains multiple Availability Zones. You can refer to this [document](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/RegionsAndAZs.html) for a deeper understanding, but we won't go into detail here.

The closer your instance is to your target audience, the lower their website loading latency will generally be. Since my target audience is primarily in Asia, I've placed my instance in Tokyo.

Next, select the instance image. This determines the operating system and any pre-installed software for your instance:

{{< image src="lightsail-image.png" alt="Lightsail Pick your instance image screen with the Linux/Unix platform selected and Ubuntu 22.04 LTS chosen as the blueprint" caption="Choosing a Lightsail Instance Image" >}}

Here, I just want a clean installation of the Ubuntu 22.04 OS. The "Optional" fields below can be left empty.

Then, you need to choose the hardware specifications for your instance. This depends on your individual needs. Since I'm only creating a personal blog and don't expect massive traffic spikes, a $5 or $10 per month plan is more than sufficient:

{{< image src="lightsail-spec.png" alt="Lightsail Choose your instance plan screen showing monthly price tiers from 3.5 to 40 USD, with the 10 USD plan (2 GB RAM, 2 vCPUs, 60 GB SSD) selected" caption="Choosing the Lightsail Instance hardware plan" >}}

Finally, give your instance a name. Since this instance is for a WordPress site, I've named it accordingly:

{{< image src="instance-name.png" alt="Lightsail Identify your instance screen with the instance named Ubuntu-Wordpress and a quantity of 1" caption="Give your instance a name" >}}

Once all the settings are configured, click the final "Create Instance" button. If you see the screen below, you have successfully created an instance on Lightsail!

{{< image src="lightsail-instance.png" alt="Lightsail dashboard card showing the Ubuntu-Wordpress instance with 2 GB RAM, 2 vCPUs and 60 GB SSD in a Running state in Tokyo Zone A" caption="Successfully created an instance on Lightsail" >}}

## Install a Web Server (Nginx)

Congratulations on completing the first two steps! You're getting close. In this third step, we need to install a web server on the instance we just created. We'll be using Nginx.

First, click on the instance you just created and connect to it via SSH:

{{< image src="connect-to-instance.png" alt="Ubuntu-Wordpress instance detail page on the Connect tab, offering a Connect using SSH button for the browser-based SSH client" caption="Connecting to the instance" >}}

If you see the following screen, you have successfully connected to the instance via SSH. From now on, you can do anything you want with this instance! :D

{{< image src="ssh-connection.png" alt="Terminal showing a successful SSH login to Ubuntu 22.04.1 LTS with system information such as load, memory and disk usage, ending at the ubuntu shell prompt" caption="Successfully connected to the instance via SSH" >}}

Next, execute the following commands to enable the Ubuntu firewall (UFW) and allow SSH connections:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

Check the current firewall status:

```bash
sudo ufw status
```

Now, install the Nginx web server on the instance:

```bash
sudo apt update
sudo apt install nginx```

After installation, remember to configure the firewall to allow HTTP and HTTPS traffic:

```bash
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
```

At this point, if you enter your instance's Public IP into your browser's address bar and see the following page, your web server is set up successfully:

{{< image src="nginx-welcome.png" alt="Browser showing the default Welcome to nginx! page confirming the web server is installed and working" caption="Accessing the Nginx welcome page by entering the Public IP in the browser" >}}

## Install a Database Management System (MySQL)

With a web server in place, you can now handle requests from all over the world, allowing people to access your site via HTTP/HTTPS. Next, we need to install a DBMS (Database Management System). A DBMS is used to manage databases, which will store your WordPress posts, pages, and other information. We'll choose MySQL for our DBMS.

Execute the following command to install MySQL:

```bash
sudo apt install mysql-server
```

After the installation is complete, enter the MySQL interface:

```bash
sudo mysql
```

Enter the following SQL command to change the root user's password (remember to replace `SetRootPasswordHere` with your own password):

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'SetRootPasswordHere';
```

If you see "Query OK," the SQL statement was executed successfully.

Exit MySQL:

```sql
exit;
```

Next, run the MySQL secure installation script:

```sql
sudo mysql_secure_installation
```

You will need to answer the following questions:

1.  **Enter password for user root:** Enter the password you just set for the root user.
2.  **Would you like to setup VALIDATE PASSWORD component?** Enter `y`.
3.  **Please enter 0 = LOW, 1 = MEDIUM and 2 = STRONG:** Enter `2`.
4.  My screen then showed **Estimated strength of the password: 100**, indicating the strength of the password I set for the root user.
5.  **Remove anonymous users?** Enter `y`.
6.  **Disallow root login remotely?** Enter `y`.
7.  **Remove test database and access to it?** Enter `y`.
8.  **Reload privilege tables now?** Enter `y`.

## Create a Dedicated Database for WordPress in MySQL

Now that MySQL is installed, we need to create a dedicated database for the WordPress site we are about to set up. Information for your WordPress site will be stored in this database.

Enter MySQL (you'll be prompted for the root user password you set):

```bash
sudo mysql -p
```

Create the WordPress database:

```sql
CREATE DATABASE wordpress DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;
```

Next, create a user in MySQL and set a password for this user (replace `your_strong_password` with your own password):

```sql
CREATE USER 'wordpress-user'@'localhost' IDENTIFIED BY 'your_strong_password';
```

To see all users in MySQL, you can run:

```sql
SELECT user FROM mysql.user;
```

If you encounter the following error when creating the user:

```text
ERROR 1819 (HY000): Your password does not satisfy the current policy requirements
```

This means the password is not strong enough. You can run the following command to check the password requirements:

```sql
SHOW VARIABLES LIKE 'validate_password%';
```

After creating the user, grant it all privileges to operate on the `wordpress` database:

```sql
GRANT ALL PRIVILEGES ON `wordpress`.* TO "wordpress-user"@"localhost";
```

Exit MySQL:

```sql
FLUSH PRIVILEGES;
exit;
```

## Install PHP

At this point, we have installed Nginx (Web Server) and MySQL (DBMS). The final piece is to install PHP. This is crucial because WordPress itself is primarily written in PHP. To run WordPress, this machine must be able to execute PHP code.

Install PHP and related extensions:

```bash
sudo apt install php-curl php-gd php-intl php-mbstring php-soap php-xml php-xmlrpc php-zip php-fpm php-mysql php-bcmath php-imagick
```

Next, you need to restart the PHP-FPM process. First, check your installed PHP version:

```bash
php -v
```

My current PHP version is 8.1.2, so I run:

```bash
sudo systemctl restart php8.1-fpm
```

## Configure Nginx

Although we have a web server, we haven't configured it yet. We haven't even told it where the website's files are located. As a result, it will only display the default welcome page when it receives a request.

First, create a new configuration file in the specified path and open it with the nano editor:

```bash
sudo nano /etc/nginx/sites-available/wordpress
```

Copy the following content into the file (pay close attention to ensure the PHP-FPM version is correct):

```nginx
server {
        listen 80;
        root /var/www/wordpress;
        index index.php index.html index.htm index.nginx-debian.html;
        # server_name myexampleblog.com www.myexampleblog.com;

        location / {
                try_files $uri $uri/ /index.php$is_args$args;
        }
        location = /favicon.ico { log_not_found off; access_log off; }
        location = /robots.txt { log_not_found off; access_log off; allow all; }
        location ~* \.(css|gif|ico|jpeg|jpg|js|png)$ {
                 expires max;
                 log_not_found off;
        }
        location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        }

        location ~ /\.ht {
                deny all;
        }
}
```

To enable this server block, you need to create a symbolic (soft) link from this file to the `sites-enabled` directory:

```bash
sudo ln -s /etc/nginx/sites-available/wordpress /etc/nginx/sites-enabled/
```

And remove the default configuration file from the `sites-enabled` directory:

```bash
sudo unlink /etc/nginx/sites-enabled/default
```

Finally, test your Nginx configuration for syntax errors:

```bash
sudo nginx -t
```

## Download WordPress

Switch to the `/tmp` directory and download the latest version of WordPress:

```bash
cd /tmp
curl -LO https://wordpress.org/latest.tar.gz
tar xzvf latest.tar.gz
```

Copy the extracted `wordpress` directory contents to the website root directory we specified in the Nginx configuration:

```bash
sudo cp -a /tmp/wordpress/. /var/www/wordpress
```

Also, remember to set the owner and group of this root directory to `www-data`:

```bash
sudo chown -R www-data:www-data /var/www/wordpress
```

Next, create a copy of the sample configuration file and edit its contents:

```bash
sudo cp /var/www/wordpress/wp-config-sample.php /var/www/wordpress/wp-config.php
sudo nano /var/www/wordpress/wp-config.php
```

Visit [this website](https://api.wordpress.org/secret-key/1.1/salt/) to generate unique phrases and fill them in below:

```php
define( 'AUTH_KEY',         'put your unique phrase here' );
define( 'SECURE_AUTH_KEY',  'put your unique phrase here' );
define( 'LOGGED_IN_KEY',    'put your unique phrase here' );
define( 'NONCE_KEY',        'put your unique phrase here' );
define( 'AUTH_SALT',        'put your unique phrase here' );
define( 'SECURE_AUTH_SALT', 'put your unique phrase here' );
define( 'LOGGED_IN_SALT',   'put your unique phrase here' );
define( 'NONCE_SALT',       'put your unique phrase here' );
```

Additionally, for WordPress to connect to the database successfully, you need to enter the following database information:

```php
define( 'DB_NAME', 'wordpress' ); // The database name we created
define( 'DB_USER', 'wordpress-user' ); // The user we created
define( 'DB_PASSWORD', 'your_strong_password' ); // The password for the user
```

Finally, save and close the file.

## WordPress Site Setup

Congratulations, you've reached the final step!

Restart Nginx:

```bash
sudo systemctl restart nginx
```

Enter your instance's Public IP in your browser. If you see the following page, it means Nginx is successfully running the WordPress application:

{{< image src="install-wordpress.png" alt="WordPress installation wizard first screen with the WordPress logo and a language selection list, English (United States) highlighted, and a Continue button" caption="Installing WordPress" >}}

From here, just follow the on-screen instructions of the WordPress installer, and your WordPress site will be live!

## Appendix

So far, we've been using the browser-based SSH client. However, I prefer to SSH into my instance from my Mac's Terminal, rather than having to open Chrome, log into AWS, and navigate to Lightsail every time (it's too cumbersome). Here’s how you can do that.

First, go to the "Networking" tab and click "Attach static IP" under the "Public IP" section:

{{< image src="set-static-ip.png" alt="Lightsail Networking tab showing IPv4 networking with public and private IP boxes and an Attach static IP link" caption="Set a Static IP for your Instance" >}}

Give your static IP a name and attach it to your current instance:

{{< image src="static-ip-name.png" alt="Lightsail Create and attach a static IP dialog with the static IP named Ubuntu-Wordpress-IP and a Create and attach button" caption="Name your Static IP" >}}

This prevents the Public IP from changing if the instance reboots.

After that, go back to the "Connect" tab and click "Download default key" at the bottom:

{{< image src="ssh-key.png" alt="Lightsail Connect tab showing the Use your own SSH client section with user name ubuntu and a Download default key link" caption="Download the Instance's Default Key" >}}

On your local machine, you will use the provided username, Public IP, and this SSH key to connect to the instance. On your local terminal, change the permissions of the downloaded `.pem` file to 400:

```bash
chmod 400 LightsailDefaultKey-ap-northeast-1.pem
```

Finally, you can connect to your instance via SSH:

```bash
ssh -i LightsailDefaultKey-ap-northeast-1.pem ubuntu@PUBLIC_IP
```

## Conclusion

In this article, we used AWS's [Lightsail](https://aws.amazon.com/lightsail/) service to get our own server/instance. We then installed Nginx (Web Server), MySQL (DBMS), and WordPress on it to successfully create our own WordPress website.

Building a website this way gives us a much higher degree of control. We can configure the server with more flexibility (e.g., the firewall) and make custom modifications to the WordPress source code.

Best of all, we can perform comprehensive backups of our site without relying on WordPress plugins! In the upcoming article, "Lightsail x WordPress: Backing Up and Restoring Your WordPress Site," I will show you how to back up and restore your website.
