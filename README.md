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
   * [Implementing Branch Protections](#implementing-branch-protections)
   * [Create Issue](#create-issue)
   * [Deploying the Web Service](#deploying-the-web-service)
6. [Conclusion](#conclusion)
   * [Production Improvements](#production-improvements)


## Overview

Locking down your repositories with the proper protections is a crucial step to ensure secure workflows are met within an organization, while still allowing for seamless and efficient collaboration.  To help make sure these rules are always set, I've created a web service in Python that listens for any new repositories created within an organization and automatically applies the protection of the master branch.  The web service then creates an issue within the repository to inform its creator of the applied protections.

The general workflow for this web service is outlined below:

    1. Set up the necessary accounts in GitHub and Heroku
    2. Set up the organization web hook
    3. Set up web service
       - Implement automatic branch protections using GitHub API
       - Create new issue outlining protections
    4. Deploy web service to Heroku

## Initial Setup

#### Requirements

* a Github account
* an organization within Github
* a repository for the web service (as well as new repositories to test)
* Heroku web server

#### Organization

You will need to create an organization within Github to host your web service, as well as to apply protection to any new repositories.  Steps on how to create an organization can be found [here](https://help.github.com/en/articles/creating-a-new-organization-from-scratch).

#### Repository

Once you have an organization, you will need to create an initial repository for the codebase of the web service.  Steps on how to create a repository can be found [here](https://help.github.com/en/articles/creating-a-new-repository).  

In the repository, you will need to commit the initial directory for the web service.  A good starting point for the web service directory can be found in an existing [repository](https://github.com/Mariatta/github-bot-tutorial/blob/master/gidgethub-for-webhooks.rst#create-a-webservice) which uses the library gidgethub to interact with the Github API.  From this tutorial, you create a file within the directory called `requirements.txt`.  In this file, you'll want to list the following dependencies:

```
aiohttp
gidgethub
```

In the root directory, you then should create a new `webservice` directory.  In this directory, create the file `__main__.py`.  For now, you can leave this empty, but this is where you will later create the actual web service.

## Heroku Setup  

In the root web service directory, you will also want to create a file named `Procfile`.  This file will instruct Heroku how to run the app. In the file, add:

```web: python3 -m webservice```

If you don't have a Heroku account, you will need to [make one](signup.heroku.com) before continuing.  Once logged into your Heroku account, you'll want to create a new web app from the [dashboard](https://dashboard.heroku.com/apps):  

![](/Assets/heroku_new_app.gif)

Then, navigate to the `Deploy` tab where you will connect your GitHub account and web service repository to your Heroku app:

![](/Assets/heroku_connect_github.gif)

Next, go to the `Settings` tab and scroll down to the `Domains` section to find your app URL:

![](/Assets/heroku_app_url.gif)

Record this URL for later steps.

## Creating the Webhook

In order to know when a new repository is created, the web service will need to receive organization web hooks from GitHub.  For those unfamiliar with web hooks, they are essentially a way for an application to provide other applications with real-time information--more information can be found [here](developer.github.com/webhooks).  

Web hooks can be configured in the `Settings` option of your organization:

![](/Assets/webhook.gif)

Please enter a random string of characters for your secret token as it will be used to secure you web hook with Heroku.  (I typically recommend using a password manager like LastPass to store these tokens).  More information on securing your web hook can be found [here](https://developer.github.com/webhooks/securing/).  You will also need to ensure you select the `Repositories` trigger as we want to be notified any time a new repo is created.

#### Authorization and Permissions

To ensure our web service properly authenticates with Github, we need to both ensure our security tokens are entered in Heroku and verify the proper permissions are in place.

For Heroku, we will need to register both `GH_SECRET` and `GH_AUTH` variables.  The `GH_SECRET` token will be the security token created in the previous step.  The `GH_AUTH` token is a `Personal Access Token` that will need to be generated from your profile settings:

![](/Assets/personal_access_token.gif)

:bangbang: Note, once you create your Personal Access Token, you will not be able to access it after you navigate off the initial page.  Similar to the `GH_SECRET`, I recommend saving this in a secure password manager.  More information on GitHub Personal Access Tokens can be found [here](https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line).

Also, you will need to choose the `repo` scope for your token.  Once you have both tokens, you need to enter both as global variables in your Heroku app settings:

![](/Assets/heroku_config_vars.gif)

## Web Service Setup

It's now time to create the actual web service.  To start editing the `__main__.py` file, we will reference the setup again described in the [github-bot-tutorial](https://github.com/Mariatta/github-bot-tutorial/blob/master/gidgethub-for-webhooks.rst#your-first-github-bot).  

Edit your `__main__.py` file with the below:

```python
import os
# asynchronous HTTP Client/Server framework (minimize process/thread wait time)
import aiohttp
import time

from aiohttp import web
# library to assist with making asynchronous calls to Github's API
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp

# routing used to keep logic separated for different event types
routes = web.RouteTableDef()
router = routing.Router()
    
# we are expecting a POST request from GitHub
@routes.post("/")
async def main(request):
    # read the GitHub webhook payload
    body = await request.read()

    # authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    # replace 'username' with your username
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "username",
                                  oauth_token=oauth_token)

        # call the appropriate callback for the event
        await router.dispatch(event, gh)

    # return a "Success"
    return web.Response(status=200)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
```

This will set you up to begin interacting with the GitHub web hooks and API using asynchronous calls.  As a reminder, you will need to replace the `username` string with your username in the main coroutine.

#### Implementing Branch Protections

In order to implement branch protections, we will need to look for when the web service receives web hook events for repository creations, then write the protections using the GitHub API.  This can be done using the following coroutine:

```python
@router.register("repository", action="created")
async def RepositoryEvent(event, gh, *args, **kwargs):
    # get new repository name
    url = event.data["repository"]["url"]
    # get default branch name
    branch = event.data["repository"]["default_branch"]
    # build url needed for PUT to add protections
    full_url = f'{url}/branches/{branch}/protection'
    # added as a temporary fix for race condition
    time.sleep(1)
    # necessary Accept header to use API during dev preview period
    accept = "application/vnd.github.luke-cage-preview+json"
    # coroutine to add master branch protections on repo creation
    await gh.put(full_url,
      	    data={
             	# required status checks to pass before merging
		"required_status_checks": {
    		    "strict": False,
    	     	    "contexts": []
  		},
		# enforce protections for administrators
		"enforce_admins": True,
		# require one approving review for pull request
		"required_pull_request_reviews": {
		    # specify which users can dismiss pull requests
		    "dismissal_restrictions": {
      			"users": [],
      			"teams": []
    		    },
		    # dismiss approval reviews when someone pushes new commit
		    "dismiss_stale_reviews": False,
		    # pull requests held until code owner approves
		    "require_code_owner_reviews": True,
		    # one reviewer required to approve pull request
		    "required_approving_review_count": 1
		},
		# restrict who can push to branch
		"restrictions": {
    		    "users": [],
    		    "teams": [],
    		    "apps": []
  		}
	    }, accept=accept)
```

There are several important elements to understand from above: 

* `event` represents the web hook received from GitHub.  Information on the payload of a repository web hook event can be found [here](https://developer.github.com/v3/activity/events/types/#repositoryevent).
* `gh` is the gidgethub API used to make API calls to GitHub.
* `full_url` is the URL used to update branch protections.  The necessary URL is constructed from information provided in the payload of the `event`.
* `accept` sets the custom media type in the Accept header.  This is required as this API call is currently only available for developers to preview.
* `put` is the method used to make the API call to the URL.  Here is where we list the protections we want to apply to the newly created master branch.

Additional details on the appropriate URL, Accept header, and PUT method to update branch protections can be found [here](https://developer.github.com/v3/repos/branches/#update-branch-protection).

You'll also see a `sleep` command in the coroutine.  This is used to mediate a potential race condition between writing the protections of the branch and the actual creation of the master branch.  We want to ensure that the master branch is fully created before attempting to write any protections to it.

#### Create Issue

We also want to create a new issue that automatically notifies the user of the protections set on the new repository.  To do this, you can add the following code to the end of the `RepositoryEvent` coroutine:

```python
    # url needed for POST to create issue
    issue_url = f'{url}/issues'
    # get username
    username = event.data["sender"]["login"]
    #nested formatted message for protections
    nested = (
	f"* Required status checks:  `None`<br>"
	f"* Enforce restrictions for Administrators: `Yes`<br>"
	f"* Users that can dismiss Pull requests: `None`<br>"
	f"* Dismiss Pull request approvals after new commit: `No`<br>"
	f"* Require code owner review: `Yes`<br>"
	f"* Number of reviewers required to approve pull request: `1`<br>"
	f"* Restrict who can push to branch: `No`<br>"
    )
    # formatted message
    message = (
	f"***Automated Branch Protections Enforced***<br><br>"
	f"@{username}, the following protections were added to the master branch:<br>"
	f"<details><summary>Enforced Protections</summary><br>{nested}</details>"
	f"***Message brought to you by Newman bot***"
	f"<details><summary>:robot:</summary><br>![Image of Newman](https://media.tenor.com/images/b54ce11a318ffd1354b74ff53d0cb001/raw)</details>"
    )
    # coroutine to create new issue
    await gh.post(issue_url,
              data={
                  'title': 'New Branch Protections Added',
                  'body': message           
              })
```

TODO: Important parts (link to create action page, link_url, formatted markdown message, POST)

#### Deploying the Web Service

Now that `__main__.py` is complete, we can proceed to deploy the web service to Heroku.  On the bottom of the `Deploy` tab in Heroku, you'll find the `Manual Deploy` section.  From here, you'll be able to choose the appropriate branch to deploy:

![](/Assets/heroku_deploy.gif)

Once the web service is successfully deployed, create a new repository within your organization.  You'll find a branch protection rule already made and a new issue listing the protections set:

![](/Assets/final.gif)

## Conclusion

TODO

#### Production Improvements

* Adjust protections set on a per client basis
* Find a more eloquent solution to the race condition
* Potentially implement rate limiting for security
* Error handling
* Be able to automatically add protections for pre-existing repositories as well
