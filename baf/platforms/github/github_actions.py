from aiohttp import ClientSession
from gidgethub.aiohttp import GitHubAPI

from baf.platforms.github.github_objects import Issue, User


async def open_issue(name: str, token: str, user: str, repository: str, title: str, body: str):
    async with ClientSession() as session:
        gh_api = GitHubAPI(session, name, oauth_token=token)
        return await gh_api.post(f'/repos/{user}/{repository}/issues',
                                data={
                                    'title': title,
                                    'body': body,
                                })


async def get_issue(name: str, token: str, user: str, repository: str, issue_number: int):
    async with ClientSession() as session:
        gh_api = GitHubAPI(session, name, oauth_token=token)
        return await gh_api.getitem(f'/repos/{user}/{repository}/issues/{issue_number}')


async def comment_issue(name: str, token: str, issue: Issue, content: str):
    async with ClientSession() as session:
        gh_api = GitHubAPI(session, name, oauth_token=token)
        return await gh_api.post(issue.comments_url.removeprefix('https://api.github.com'),
                            data={
                                'body': content,
                            })


async def set_label(name: str, token: str, issue: Issue, label: str):
    labels_names = list(map(lambda l: l['name'], issue.labels))
    if label not in labels_names:
        labels_names.append(label)
        issue.labels.append({'name' : label})
        async with ClientSession() as session:
            gh_api = GitHubAPI(session, name, oauth_token=token)
            return await gh_api.put(issue.labels_url.removeprefix('https://api.github.com'),
                               data={
                                   'labels': labels_names
                               })


async def assign_user(name: str, token: str, issue: Issue, assignee: str):
    assignees_names = list(map(lambda u: u.login, issue.assignees))
    if assignee not in assignees_names:
        assignees_names.append(assignee)
        issue.assignees.append(User({
          "login": assignee,
          "id": 0,
          "html_url": f"https://github.com/{assignee}",
          "organizations_url": f"https://api.github.com/users/{assignee}/orgs",
          "repos_url": f"https://api.github.com/users/{assignee}/repos"
        }))
        async with ClientSession() as session:
            gh_api = GitHubAPI(session, name, oauth_token=token)
            return await gh_api.post(issue.assignees_url.removeprefix('https://api.github.com'),
                                data={
                                    'assignees': assignees_names,
                                })
