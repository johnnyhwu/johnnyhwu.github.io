---
# weight: 1
title: "WordPress Backup and Migration Guide: How to Manually Restore Your Site on a New Server"
date: 2023-08-02
lastmod: 2025-09-20
draft: false
description: "Learn how to back up and restore your WordPress website with our step-by-step guide. Use simple SSH and MySQL commands to protect your files and database, preventing data loss and making server migrations easy."
featuredImage: "featured-image.png"

tags: ["AWS", "Nginx", "WordPress"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## Introduction

In the article "[How to Create Your Own Website with AWS Lightsail and WordPress](../aws-lightsail-wordpress/)," we covered how to use AWS's [Lightsail](https://aws.amazon.com/lightsail/) service to get your own Server/Instance. We then installed Nginx (Web Server), MySQL (DBMS), and WordPress on that instance to successfully launch a WordPress website.

Once you have your own website, "backing up the site" becomes an incredibly important task. You certainly don't want to see all your hard work go down the drain. Therefore, this article will build upon the WordPress site created in the [previous article](../aws-lightsail-wordpress/) to teach you how to back up and restore your website! In fact, as long as you can **SSH into your server**, the instructions in this article will apply to you.

## Backing Up a WordPress Site

Compared to site restoration, backing up a website is quite simple! You only need to back up the "website root directory" and the "database." First, backing up the site root directory means compressing `/var/www/wordpress` into a ZIP file:

```bash
sudo apt install zip
zip -r wordpress.zip /var/www/wordpress/
```

Next, perform a dump of the WordPress database in MySQL:

```bash
mysqldump -u wordpress-user -p --opt wordpress --no-tablespaces > wordpress.sql
```

After these two steps, you will have "wordpress.zip" and "wordpress.sql" in your current directory. You need to use SCP to transfer them back to your own computer:

```bash
scp -i [path to pem file] ubuntu@[public IP]:[path to wordpress.sql] .
scp -i [path to pem file] ubuntu@[public IP]:[path to wordpress.zip] .
```

## Restoring a WordPress Site

The site restoration process is basically the same as the backup process, just in reverse! First, install the unzip tool on Ubuntu:

```bash
sudo apt install unzip
```

Unzip the site root directory you just obtained and move it to the correct location:

```bash
unzip wordpress.zip
sudo mv wordpress /var/www/
```

Remember! In addition to moving the site root directory to the correct location, you also need to modify its permissions (we also performed this action in the [previous article](../aws-lightsail-wordpress/)):

```bash
sudo chown -R www-data:www-data /var/www/wordpress
```

After restoring the site root directory, the next step is to restore the WordPress database. This mainly involves importing `wordpress.sql` directly into an empty "wordpress" database:

```bash
mysql -u wordpress-user -p wordpress < wordpress.sql
```

At this point, you can try entering your server's Public IP into your browser's address bar. If your previous website appears successfully, it means the site has been restored! However, things are often not that simple. When we perform a site restoration, we might not be restoring it to the original server.

In other words, the backup might have been taken from Server A, but the restoration is being performed on Server B. Because Server A and Server B often have different IPs, and the backup data we currently have (`wordpress.sql`) contains references pointing to the original server's IP, our website won't display correctly even after we restore it on Server B.

If you encounter this problem, after completing the steps above, you will need to go into MySQL and make some modifications to the WordPress database. First, enter the MySQL SQL interface:

```bash
sudo mysql -p
```

Enter the root password. Next, select the WordPress database:

```bash
use wordpress;
```

Check where the domain of the WordPress site restored from another server is pointing:

```sql
SELECT * FROM wp_options WHERE option_name = 'home' OR option_name = 'siteurl';
```

If the domain shown is different from the Public IP of the current server, the WordPress site will not display correctly. Therefore, we need to replace all occurrences of the old domain in the database with the new one:

```sql
UPDATE wp_options SET option_value = replace(option_value, 'https://www.oldurl', 'https://www.newurl') WHERE option_name = 'home' OR option_name = 'siteurl';
UPDATE wp_posts SET guid = replace(guid, 'https://www.oldurl','https://www.newurl');
UPDATE wp_posts SET post_content = replace(post_content, 'https://www.oldurl', 'https://www.newurl');
UPDATE wp_postmeta SET meta_value = replace(meta_value,'https://www.oldurl','https://www.newurl');
```

Remember, in all the SQL commands above, "https://www.oldurl" should be replaced with the original WordPress site's domain, and "https://www.newurl" should be replaced with "http://[Public IP of the current server]". Finally, exit MySQL:

```sql
exit;
```

Restart the MySQL and Nginx services:

```bash
sudo systemctl restart mysql
sudo systemctl restart nginx
```

## Conclusion

"Backing up your website" is always a critical task. I once wrote many articles on my own blog, but because I forgot to pay the server rental fee for a long time, the entire server was deleted, and all my past hard work was lost. This article has shown you how to back up and restore an [existing website](../aws-lightsail-wordpress/), so you'll never have to fear losing your hard-earned work again.
