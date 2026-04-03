from aiohttp import ClientSession
from gidgetlab.aiohttp import GitLabAPI

from baf.platforms.gitlab.gitlab_objects import Issue, User


async def open_issue(name: str, token: str, user: str, repository: str, title: str, body: str):
    async with ClientSession() as session:
        gl_api = GitLabAPI(session, name, access_token=token)
        return await gl_api.post(f'/projects/{user}%2F{repository}/issues',
                                data={
                                    'title': title,
                                    'description': body,
                                })


async def get_issue(name: str, token: str, user: str, repository: str, issue_number: int):
    async with ClientSession() as session:
        gl_api = GitLabAPI(session, name, access_token=token)
        return await gl_api.getitem(f'/projects/{user}%2F{repository}/issues/{issue_number}')


async def comment_issue(name: str, token: str, issue: Issue, content: str):
    async with ClientSession() as session:
        gl_api = GitLabAPI(session, name, access_token=token)
        return await gl_api.post(issue.comments_url.removeprefix('https://gitlab.com/api/v4'),
                            data={
                                'body': content,
                            })


async def set_label(name: str, token: str, issue: Issue, label: str):
    issue.labels.append({'name': label})
    async with ClientSession() as session:
        gl_api = GitLabAPI(session, name, access_token=token)
        return await gl_api.put(issue.labels_url.removeprefix('https://gitlab.com/api/v4'),
                           data={
                               'add_labels': [label]
                           })


async def assign_user(name: str, token: str, issue: Issue, assignee_id: int):
    assignee_ids = list(map(lambda u: u.id, issue.assignees))
    if assignee_id not in assignee_ids:
        assignee_ids.append(assignee_id)
        issue.assignees.append(
            User({"username": "",
                "id": assignee_id,
                "web_url": f"https://gitlab.com/user-{assignee_id}"
        }))
        async with ClientSession() as session:
            gl_api = GitLabAPI(session, name, access_token=token)
            return await gl_api.put(issue.assignees_url.removeprefix('https://gitlab.com/api/v4'),
                                data={
                                    'assignee_ids': assignee_ids,
                                })
