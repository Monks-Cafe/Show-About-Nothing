import os
import aiohttp

from aiohttp import web
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp

routes = web.RouteTableDef()
router = routing.Router()

@router.register("repository", action="created")
async def RepositoryEvent(event, gh, *args, **kwargs):
    """ Whenever a repository is created, automate the protection of the master branch"""

    # get new repository name
    newrepo = event.data["repository"]["name"]
    branch = event.data["repository"]["default_branch"]
    owner = event.data["repository"]["owner"]["login"]
    endpoint = f'/repos/{owner}/{newrepo}/branches/{branch}/protection'
    print(endpoint)
    #add master branch protections
    await gh.post(endpoint,
             data={
             	# required status checks to pass before merging
		"required_status_checks": {},
		# enforce protections for administrators
		"enforce_admins": True,
		# require one approving review for pull request
		"required_pull_request_reviews": {
		# specify which users can dismiss pull requests
		"dismissal_restrictions": {},
		# dismiss approving reviews when someone pushes new commit
		"dismiss_stale_reviews": False,
		# pull requests held until code owner approves
		"require_code_owner_reviews": True,
		# one reviewer required to approve pull request
		"required_approving_review_count": 1
		},
		# restrict who can push to branch
		"restrictions": {}
		})

@routes.post("/")
async def main(request):
    # read the GitHub webhook payload
    body = await request.read()

    # authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    # add username
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
