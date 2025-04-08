from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web_request import Request
from gidgethub import sansio

from besser.agent.library.coroutine.async_helpers import sync_coro_call
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms import github
from besser.agent.platforms.github.github_actions import *
from besser.agent.platforms.github.github_objects import Issue
from besser.agent.library.transition.events.github_webhooks_events import GitHubEvent
from besser.agent.platforms.payload import Payload
from besser.agent.platforms.platform import Platform

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class GitHubPlatform(Platform):
    """The GitHub Platform allows an agent to receive events from GitHub webhooks and make calls to its REST API

    This platform implements a webserver exposing an endpoint to receive webhooks events from GitHub.
    In addition, the platform provides abstractions for interacting with issues (e.g., open, get, comment).

    Args:
        agent (Agent): the agent the platform belongs to

    Attributes:
        _agent (Agent): The agent the platform belongs to
        _secret (str): The secret webhook token
        _oauth_token (str): Personal token for GitHub API requests
        _port (int): Port of the webhook endpoint
        _app (web.Application): Web application routing webhooks to our entrypoint
        _session (Session): The session of the GitHubPlatform
        _post_entrypoint (Request -> web.Response): The method handling the webhooks events
    """

    def __init__(self, agent: 'Agent'):
        super().__init__()
        self._agent: 'Agent' = agent
        self._secret: str = self._agent.get_property(github.GITHUB_WEBHOOK_TOKEN)
        self._oauth_token: str = self._agent.get_property(github.GITHUB_PERSONAL_TOKEN)
        self._port: int = self._agent.get_property(github.GITHUB_WEBHOOK_PORT)
        self._app: web.Application = web.Application()
        self._session: Session = None

        async def post_entrypoint(request: Request) -> web.Response:
            body = await request.read()

            event = sansio.Event.from_http(request.headers, body, secret=self._secret)
            if event.event == 'gollum':
                pages = event.data['pages']
                for page in pages:
                    agent.receive_event(GitHubEvent('gollum', page['action'], page))
            else:
                agent.receive_event(GitHubEvent(event.event, event.data['action'] or '', event.data))
            return web.Response(status=200)

        self._post_entrypoint = post_entrypoint

    def initialize(self) -> None:
        self._app.router.add_post("/", self._post_entrypoint)
        if self._port is not None:
            self._port = int(self._port)

    def start(self) -> None:
        logger.info(f'{self._agent.name}\'s GitHubPlatform starting')
        self._agent.get_or_create_session("GitHub_Session_" + str(self.__hash__()), self)
        self.running = True
        web.run_app(self._app, port=self._port, handle_signals=False)

    def stop(self):
        self.running = False
        sync_coro_call(self._app.shutdown())
        sync_coro_call(self._app.cleanup())
        logger.info(f'{self._agent.name}\'s GitHubPlatform stopped')

    def __getattr__(self, name: str):
        """All methods in :class:`aiohttp.GitHubAPI` can be used from the GitHubPlatform.

        Args:
            name (str): the name of the function to call
        """

        async def api_call(*args, **kwargs):
            async with ClientSession() as session:
                gh_api = GitHubAPI(session, self._agent.name, oauth_token=self._oauth_token)
                # Forward the method call to the GitHubAPI
                method = getattr(gh_api, name, None)
                if method:
                    return await method(*args, **kwargs)
                else:
                    raise AttributeError(f"'{gh_api.__class__}' object has no attribute '{name}'")

        def method_proxy(*args, **kwargs):
            return sync_coro_call(api_call(*args, **kwargs))

        return method_proxy

    def _send(self, session_id, payload: Payload) -> None:
        logger.warning(f'_send() method not implemented in {self.__class__.__name__}')

    def reply(self, session: Session, message: str) -> None:
        logger.warning(f'reply() method not implemented in {self.__class__.__name__}')

    def open_issue(self, user: str, repository: str, title: str, body: str) -> Issue:
        return Issue(sync_coro_call(open_issue(self._agent.name, self._oauth_token, user, repository, title, body)))

    def get_issue(self, user: str, repository: str, issue_number: int) -> Issue:
        return Issue(sync_coro_call(get_issue(self._agent.name, self._oauth_token, user, repository, issue_number)))

    def comment_issue(self, issue: Issue, content: str):
        return sync_coro_call(comment_issue(self._agent.name, self._oauth_token, issue, content))

    def set_label(self, issue: Issue, label: str):
        return sync_coro_call(set_label(self._agent.name, self._oauth_token, issue, label))

    def assign_user(self, issue: Issue, assignee: str):
        return sync_coro_call(assign_user(self._agent.name, self._oauth_token, issue, assignee))
