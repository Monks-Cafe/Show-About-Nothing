# Web Service Automating New Branch Protections

## Table of Contents
1. [Overview](#overview)
2. [Initial Setup](#initial-setup)
   * [Requirements](#requirements)
   * [Organization](#organization)
   * [Repository](#repository)
3. [Heroku Setup](#heroku-setup)
4. [Creating the Webhook](#creating-the-webhook)
   * [Authorization and Permissions](#authorization-and-permissions)
5. [Web Service Setup](#web-service-setup)
   * [Create Event from Webhook](#create-event-from-webhook)
   * [Implementing Branch Protections](#implementing-branch-protections)
   * [Create Issue](#create-issue)
   * [Troubleshooting](#troubleshooting)
6. [Conclusion](#conclusion)
   * [Production Improvements](#production-improvements)


## Overview

Locking down your repositories is a crucial step to ensure code security within an organization, even among the members of the organization itself.  To help make sure these rules are always set, I've created a web service that listens for any new repositories created within an organization and automatically applies the protection of the master branch.  The web service will also create a new issue within the repository listing the applied protections.

## Initial Setup

### Requirements

    * a Github account
    * an organization within Github
    * a repository for the web service
    * Heroku web server

### Organization

You will need to create an organization within Github to apply protections to any new repositories.  Steps on how to create an organization can be found [here](https://help.github.com/en/articles/creating-a-new-organization-from-scratch).

### Repository

Once you have an organization, you will need to create an initial repository for the codebase of the web service.  Steps on how to create a repository can be found [here](https://help.github.com/en/articles/creating-a-new-repository).  

In the repository, you will need to commit the initial directory for the web service.  A good starting point for the web service directory can be found in an existing [repository](https://github.com/Mariatta/github-bot-tutorial/blob/master/gidgethub-for-webhooks.rst#create-a-webservice) which uses the library gidgethub to interact with the Github API.  From this tutorial, you create a file within the directory called `requirements.txt`.  In this file, you'll want to list the following dependencies:

```
aiohttp
gidgethub
```

In the root directory, you then create a new `webservice` directory.  In this directory, create the file `__main__.py`.  This is where you will later create the web service.

## Heroku Setup

In the root web service directory, you will also want to create a file named `Procfile`.  This file will instruct Heroku how to run the app. In the file, add:

```web: python3 -m webservice```

Once logged into your Heroku account, you'll want to create a new web app from the [dashboard](https://dashboard.heroku.com/apps):  

![](/Assets/heroku_new_app.gif)

Then connect your Github account from the `Deploy` tab:

![](/Assets/heroku_connect_github.gif)

Next, go to the `Settings` tab and scroll down to the `Domains` section to find your app URL:

![](/Assets/heroku_app_url.gif)



## Creating the Webhook
### Authorization and Permissions
## Web Service Setup
### Create Event from Webhook
### Implementing Branch Protections
### Create Issue
### Troubleshooting
## Conclusion
### Production Improvements
