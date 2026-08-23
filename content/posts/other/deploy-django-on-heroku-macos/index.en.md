---
# weight: 1
title: "Deploying a Django App to Heroku on macOS"
date: 2023-02-06
lastmod: 2023-02-06
draft: false
description: "A hands-on Heroku deployment walkthrough: create a conda virtual environment on macOS, install Django and gunicorn, and push a brand-new Django app live on Heroku step by step."
featuredImage: "featured-image.jpg"

tags: ["Heroku", "Django", "Python"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

{{< image src="heroku-banner.jpg" alt="Heroku's brand visual, used as the opening image of this deployment tutorial." caption="Deploying a Django app to Heroku (image source: Heroku)" >}}

## Introduction

Once you've finished building a site on your local server, the next step is usually to make it public so other people can actually reach it. The trouble is that renting a machine, setting up the OS, and configuring a web server and database is a lot of overhead for someone who just wants to put a project online.

To shorten that path, a number of "Platform as a Service" (PaaS) tools have shown up — you push your code, and the platform takes care of the rest of the environment. This post uses Heroku as the example, walking from creating a virtual environment all the way through to deploying a brand-new Django app to the cloud. Everything here is done on macOS, and you can follow the commands directly.

## What Is Heroku?

{{< image src="heroku-paas-overview.jpg" alt="A brand illustration of Heroku's platform service." caption="Heroku is a container-based PaaS platform (image source: Heroku)" >}}

Heroku is a container-based "Platform as a Service" (PaaS). Developers can quickly deploy applications to Heroku and let Heroku manage the application's resource usage. That means software developers don't need to deal directly with managing hardware resources, which lowers the barrier to deploying software.

Put simply, there are only two things you need to do: organize your code into a Git repo, and tell Heroku what packages the app needs and what command to run it with. Once Heroku reads that information, it builds the runtime environment for you automatically.

## Deploying a Django App to Heroku

Now that we've covered the basics of Heroku, let's walk through the full process. We'll start by creating a virtual environment with conda, and the whole flow breaks down into 6 steps:

1. Create a virtual environment
2. Install the required packages
3. Create the Django project
4. Add the files Heroku needs
5. Initialize a local repo
6. Push to Heroku to finish the deployment

## Step 1: Create a Virtual Environment with conda

To keep projects isolated from one another, we'll use conda to create a virtual environment that contains only the packages Django and Heroku need. This matters later, in Step 4: we'll hand Heroku the environment's package list via `pip freeze`, and if we used the system Python environment directly, that list would get polluted with a bunch of packages unrelated to this project.

Inside the virtual environment conda creates, we still install packages via pip, so if you don't have conda installed, that's fine too — you can use [virtualenv](https://pypi.org/project/virtualenv/) to create the virtual environment instead, and the rest of the steps stay exactly the same.

First, open a terminal and run the following command to create a virtual environment named DjangoHeroku with Python 3.9.

```bash
conda create --name DjangoHeroku python=3.9
```

Then, activate this virtual environment.

```bash
conda activate DjangoHeroku
```

At this point, your terminal prompt should now be prefixed with `(DjangoHeroku)`. That prefix is the most direct way to tell whether you're currently inside the virtual environment or not.

## Step 2: Install the Required Packages

In this step, we need to use pip to install a few packages so the Django app can be deployed to Heroku successfully. First, check the current pip version and its location.

```bash
pip --version
```

You should see something like this:

```text
pip 21.2.4 from /Users/xxxxx/miniforge3/envs/DjangoHeroku/lib/python3.9/site-packages/pip (python 3.9)
```

The thing to check here is the `envs/DjangoHeroku` segment in the middle of the path — it confirms you're really using the pip inside the virtual environment, not the system one. If the path looks wrong, go back and make sure you ran `conda activate`.

Next, install the django package.

```bash
pip install django
```

Install the gunicorn package. gunicorn is the production-grade WSGI server, and Heroku will use it to run our app instead of Django's built-in development server.

```bash
pip install gunicorn
```

Next up, the package we're about to install depends on the PostgreSQL driver for Python (psycopg2), so PostgreSQL needs to be installed on your machine first for that to succeed. You can download and install it from [PostgreSQL Download](https://postgresapp.com/downloads.html). Then, run the following command to install the Postgres CLI.

```bash
sudo mkdir -p /etc/paths.d && echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp
```

This command adds the executable path from Postgres.app to your system PATH, so you can call `psql` directly from the terminal afterward. Once that's done, restart your terminal and confirm PostgreSQL installed successfully.

```bash
which psql
```

Seeing the following output means the installation succeeded:

```text
/Applications/Postgres.app/Contents/Versions/latest/bin/psql
```

Since we just restarted the terminal, we need to activate the virtual environment again.

```bash
conda activate DjangoHeroku
```

Once you're back inside the virtual environment, install the django-heroku package. This package configures all the settings the Heroku environment needs in one shot — database connection, static files, logging, and so on — saving you the trouble of editing a pile of settings by hand. (This package is no longer maintained today; following along with it here is fine, since this is a historical tutorial, but if you're starting a brand-new project now, it's worth looking into alternatives.)

```bash
pip install django-heroku
```

Finally, check that all the required packages installed correctly.

```bash
pip list
```

You should see the following output, showing the installed packages:

```text
Package         Version
--------------- -------
asgiref         3.4.1
dj-database-url 0.5.0
Django          3.2.7
django-heroku   0.3.1
gunicorn        20.1.0
pip             21.2.4
psycopg2        2.9.1
pytz            2021.1
setuptools      58.0.3
sqlparse        0.4.1
wheel           0.37.0
whitenoise      5.3.0
```

Notice that we only manually installed four packages, yet the list is a lot longer than that — that's because django-heroku pulled in dj-database-url, psycopg2, and whitenoise as dependencies along the way.

## Step 3: Create the Django Project

With the necessary packages installed, we need to create a Django project before we can deploy it to Heroku. First, switch to the Desktop directory.

```bash
cd ~/Desktop
```

Create a Django project on the Desktop named MyFirstProject.

```bash
django-admin startproject MyFirstProject
```

Switch into this project's directory.

```bash
cd MyFirstProject
```

Add a new application inside the project, named myapp.

```bash
python manage.py startapp myapp
```

A quick note on Django terminology: a Project is the whole site, while an Application is one functional module underneath it — a single Project can host many Apps. At this point, MyFirstProject's structure looks like this:

{{< image src="project-structure-after-startapp.jpg" alt="A tree view of the Django project folder, showing manage.py, the settings folder of the same name, and the newly created myapp folder under MyFirstProject." caption="The project folder's contents (after creating MyFirstProject and myapp)" >}}

Next, we need to make a few edits to settings.py inside the MyFirstProject/MyFirstProject folder. First, around line 13, import two more packages.

```python
import os
import django_heroku
```

Around line 35, add the app we just created to the INSTALLED_APPS list. Without this line, Django won't recognize myapp.

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp'  # add this line
]
```

Around line 124, add the STATIC_ROOT path. This is the output directory Django collects static files into, and it must be set for deployment to Heroku — otherwise your CSS and images won't be found.

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

Finally, add this line at the very end of settings.py, so django-heroku can override the settings with what the Heroku environment needs:

```python
django_heroku.settings(locals())
```

In Django, all images, CSS, and JS files live under a static folder, so add a static folder under both MyFirstProject/MyFirstProject and MyFirstProject/myapp.

```bash
mkdir MyFirstProject/static
mkdir myapp/static
```

Finally, sync up the database. The first command generates migration files based on your model definitions; the second actually applies those changes to the database.

```bash
python manage.py makemigrations
```

```bash
python manage.py migrate
```

At this point, we've finished setting up the Django project, and we can use the following command to view our site on the local server.

```bash
python manage.py runserver
```

You should see the following output:

{{< image src="django-runserver-output.jpg" alt="A terminal screen showing the startup message from the Django development server along with the local address it's listening on." caption="Running the Django server" >}}

In your browser, visit the following address to see Django's default page.

```text
http://127.0.0.1:8000/
```

{{< image src="django-default-homepage.jpg" alt="Django's default welcome page in a browser, showing the success message and a rocket illustration." caption="Django's default home page" >}}

Seeing this page confirms your Django project was set up correctly. Back in the terminal, press Ctrl+C to stop the local server.

## Step 4: Add the Files Heroku Needs

Now that the Django project is up and running, we still need to prepare a few files so Heroku knows what packages to install and what command to run our app with. This step is the bridge between local development and cloud deployment: on your own machine, all of this information is tucked away inside the virtual environment, which Heroku can't see — so it has to be written out to files instead.

First, check the current project structure:

{{< image src="project-structure-before-heroku-files.jpg" alt="A tree view of the Django project folder, before Procfile, requirements.txt, and runtime.txt have been added." caption="The project folder's contents (before adding Heroku's required files)" >}}

Next, run the following command to generate a Procfile. A Procfile consists of `<process type>: <command>` entries that tell Heroku what command to run for our app. Here, `web` means this is a process that receives HTTP requests from outside, followed by the command that starts MyFirstProject's WSGI app with gunicorn.

```bash
echo 'web: gunicorn MyFirstProject.wsgi' > Procfile
```

We also need to tell Heroku which packages our app depends on. `pip freeze` writes every package in the virtual environment, along with its version, into requirements.txt, and Heroku installs from that list when it builds.

```bash
pip freeze > requirements.txt
```

Finally, we need to tell Heroku which Python version we're using.

```bash
python --version
```

This gives:

```text
Python 3.9.7
```

Generate a runtime.txt with the Python version written inside. Note the format is `python-` followed by the version number, not the raw output pasted directly.

```bash
echo 'python-3.9.7' > runtime.txt
```

Check the project structure once more — it should now have the three files we just generated:

{{< image src="project-structure-after-heroku-files.jpg" alt="A tree view of the Django project folder, now including Procfile, requirements.txt, and runtime.txt." caption="The project folder's contents (after adding Procfile, requirements.txt, and runtime.txt)" >}}

## Step 5: Initialize a Local Repo

With the files Heroku needs in place, we need to turn the whole Django app project into a local repo. Heroku's deployment model is "git push" — so from now on, any change in the project just needs the repo pushed again to trigger a redeploy. (If you install any new packages, remember to regenerate requirements.txt, or Heroku won't know about the new dependency.)

Initialize the local repo:

```bash
git init
git add .
git commit -m "create django app"
```

## Step 6: Deploy the Django App to Heroku

In this final step, we'll push the local repo to the remote repo on Heroku's platform, completing the Django app's deployment.

First, sign up for an account at [Heroku](https://signup.heroku.com/). (The original tutorial mentioned a free account, but Heroku discontinued its free tier in November 2022, so you'll need a paid plan to actually run this today.) Next, log in to Heroku from the terminal as well.

```bash
heroku login
```

Press Enter and you'll be able to log in through your browser. Then, create an app on Heroku named my-first-project-django. Note that Heroku app names are unique across the entire platform, so you'll need to pick a name that isn't already taken — and use that same name in the following commands and URLs.

```bash
heroku create my-first-project-django
```

Next, configure where the local repo should actually be pushed to.

```bash
heroku git:remote -a my-first-project-django
```

This gives:

```text
set git remote heroku to https://git.heroku.com/my-first-project-django.git
```

Finally, push our local repo up.

```bash
git push heroku master
```

At this point, Heroku builds the environment based on the Procfile, requirements.txt, and runtime.txt in the local repo. The entire build process is printed directly to the terminal, so if any package fails to install, you'll see the error there. In the end, you'll get the URL your app is deployed at on Heroku:

```text
https://my-first-project-django.herokuapp.com/
```

Before opening the page, you also need to scale up at least 1 dyno to run the app. A dyno is the container Heroku uses to run your app — with a count of 0, the app isn't running at all.

```bash
heroku ps:scale web=1
```

Once that's done, visit the URL in your browser — if you see the page below, you've successfully deployed the Django app to Heroku! This is the exact same Django default home page we saw earlier at `127.0.0.1:8000`, except now it's running in the cloud, on an address anyone can reach.

{{< image src="django-default-homepage.jpg" alt="Django's default welcome page in a browser, showing the success message and a rocket illustration." caption="Django's default home page" >}}

## Conclusion

This post walked through the full process of shipping a Django app to Heroku, starting from a conda virtual environment, through installing packages and creating the Django project, adding the Procfile / requirements.txt / runtime.txt files Heroku needs, and finally deploying with a git push.

The real key idea is a single concept: Heroku can't see the environment on your own computer, so you have to write out "what to install, how to run it, and which Python version to use" into files and hand them over. Once you understand that, moving to any other PaaS platform follows the exact same logic.
