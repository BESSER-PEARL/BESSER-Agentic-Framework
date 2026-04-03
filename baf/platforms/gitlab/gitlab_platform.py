from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from gidgetlab import sansio

from baf.library.coroutine.async_helpers import sync_coro_call
from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.platforms import gitlab
from baf.platforms.gitlab.gitlab_actions import open_issue, get_issue, comment_issue, set_label, assign_user
from baf.platforms.gitlab.gitlab_objects import Issue
from baf.library.transition.events.gitlab_webhooks_events import GitLabEvent
from baf.platforms.payload import Payload
from baf.platforms.platform import Platform

if TYPE_CHECKING:
    from baf.core.agent import Agent


class GitLabPlatform(Platform):
    """The GitLab Platform allows an agent to receive events from GitLab webhooks and make calls to its REST API

    This platform implements a webserver exposing an endpoint to receive webhooks events from GitLab.
    In addition, the platform provides abstractions for interacting with issues (e.g., open, get, comment).

    Args:
        agent (Agent): the agent the platform belongs to

    Attributes:
        _agent (Agent): The agent the platform belongs to
        _secret (str): The secret webhook token
        _oauth_token (str): Personal token for GitLab API requests
        _port (int): Port of the webhook endpoint
        _app (web.Application): Web application routing webhooks to our entrypoint
        _session (Session): The session of the GitLabPlatform
        _post_entrypoint (Request -> web.Response): The method handling the webhooks events
    """

    def __init__(self, agent: 'Agent'):
        super().__init__()
        self._agent: 'Agent' = agent
        self._secret: str = self._agent.get_property(gitlab.GITLAB_WEBHOOK_TOKEN)
        self._oauth_token: str = self._agent.get_property(gitlab.GITLAB_PERSONAL_TOKEN)
        self._port: int = self._agent.get_property(gitlab.GITLAB_WEBHOOK_PORT)
        self._app = web.Application()
        self._session: Session = None

        async def post_entrypoint(request) -> web.Response:
            body = await request.read()

            event = sansio.Event.from_http(request.headers, body, secret=self._secret)
            if event.event == "Note Hook":
                agent.receive_event(GitLabEvent(event.data['object_attributes']['noteable_type'] + event.event,
                                                event.data['object_attributes']['action'] or '', event.data))
            else:
                agent.receive_event(GitLabEvent(
                    event.event,
                    event.data['object_attributes']['action'] or '',
                    event.data))
            return web.Response(status=200)

        self._post_entrypoint = post_entrypoint

    def initialize(self) -> None:
        self._app.router.add_post("/", self._post_entrypoint)
        if self._port is not None:
            self._port = int(self._port)

    def start(self) -> None:
        logger.info(f'{self._agent.name}\'s GitLabPlatform starting')
        self._agent.get_or_create_session("GitLab_Session_" + str(self._event_loop.__hash__()), self)
        self.running = True
        web.run_app(self._app, port=self._port, handle_signals=False)

    def stop(self):
        self.running = False
        sync_coro_call(self._app.shutdown())
        sync_coro_call(self._app.cleanup())
        logger.info(f'{self._agent.name}\'s GitLabPlatform stopped')

    def __getattr__(self, name: str):
        """All methods in :class:`aiohttp.GitLabAPI` can be used from the GitLabPlatform.

        Args:
            name (str): the name of the function to call
        """

        async def api_call(*args, **kwargs):
            async with ClientSession() as session:
                gl_api = GitLabAPI(session, self._agent.name, access_token=self._oauth_token)
                # Forward the method call to the gitlab api
                method = getattr(gl_api, name, None)
                if method:
                    return await method(*args, **kwargs)
                else:
                    raise AttributeError(f"'{gl_api.__class__}' object has no attribute '{name}'")

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

    def assign_user(self, issue: Issue, assignee: int):
        return sync_coro_call(assign_user(self._agent.name, self._oauth_token, issue, assignee))
