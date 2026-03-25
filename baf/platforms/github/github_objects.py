from typing import Any


class User:
    def __init__(self, api_payload):
        self._id: int = api_payload['id']
        self._login: str = api_payload['login']
        self._profile_url: str = api_payload['html_url']
        self._organizations_url: str = api_payload['organizations_url']
        self._repos_url: str = api_payload['repos_url']

    @property
    def id(self) -> int:
        """int: The user id."""
        return self._id

    @property
    def login(self) -> str:
        """str: The user login."""
        return self._login

    @property
    def profile_url(self) -> str:
        """str: The user profile_url."""
        return self._profile_url

    @property
    def organizations_url(self) -> str:
        """str: The user organizations_url."""
        return self._organizations_url

    @property
    def repos_url(self) -> str:
        """str: The user repos_url."""
        return self._repos_url


class Issue:
    def __init__(self, api_payload):
        self._id: int = api_payload['id']
        self._number: int = api_payload['number']
        self._title: str = api_payload['title']
        self._creator: User = User(api_payload['user'])
        self._labels: list[Any] = api_payload['labels']
        self._state: str = api_payload['state']
        self._locked: bool = api_payload['locked']
        self._assignees: list[User] = list(map(lambda a: User(a),api_payload['assignees']))
        self._milestone: Any = api_payload['milestone']
        self._url: str = api_payload['url']
        self._repository_url: str = api_payload['repository_url']
        self._labels_url: str = api_payload['labels_url']
        self._comments_url: str = api_payload['comments_url']
        self._assignees_url: str = api_payload['url'] + '/assignees'
        self._events_url: str = api_payload['events_url']

    @property
    def id(self) -> int:
        """int: The issue id."""
        return self._id

    @property
    def number(self) -> int:
        """int: The issue number."""
        return self._number

    @property
    def title(self) -> str:
        """str: The issue title."""
        return self._title

    @property
    def creator(self) -> User:
        """User: The issue creator."""
        return self._creator

    @property
    def labels(self) -> list[Any]:
        """list[Any]: The issue labels."""
        return self._labels

    @property
    def state(self) -> str:
        """str: The issue state."""
        return self._state

    @property
    def locked(self) -> bool:
        """bool: The issue locked."""
        return self._locked

    @property
    def assignees(self) -> list[User]:
        """list[User]: The issue assignees."""
        return self._assignees

    @property
    def milestone(self) -> Any:
        """Any: The issue milestone."""
        return self._milestone

    @property
    def url(self) -> str:
        """str: The issue url."""
        return self._url

    @property
    def repository_url(self) -> str:
        """str: The issue repository_url."""
        return self._repository_url

    @property
    def labels_url(self) -> str:
        """str: The issue labels_url."""
        return self._labels_url

    @property
    def comments_url(self) -> str:
        """str: The issue comments_url."""
        return self._comments_url

    @property
    def assignees_url(self) -> str:
        """str: The issue assignees_url."""
        return self._assignees_url

    @property
    def events_url(self) -> str:
        """str: The issue events_url."""
        return self._events_url
