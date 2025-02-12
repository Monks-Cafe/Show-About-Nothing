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

@router.register("repository", action="created")
async def RepositoryEvent(event, gh, *args, **kwargs):
    """Whenever a repository is created, automate the protection of the master branch and create issue listing protections"""

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

# we are expecting a POST webhook
@routes.post("/")
async def main(request):
    # read the GitHub webhook payload
    body = await request.read()

    # authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    # add username auth
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "seancustodio",
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
