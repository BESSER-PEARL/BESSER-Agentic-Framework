from typing import Any


class User:
    def __init__(self, api_payload):
        self._id: int = api_payload['id']
        self._login: str = api_payload['username']
        self._profile_url: str = api_payload['web_url']
        self._groups_url: str = api_payload['web_url'] + '/groups'

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
    def groups_url(self) -> str:
        """str: The user groups url."""
        return self._groups_url


class Issue:
    def __init__(self, api_payload):
        self._id: int = api_payload['id']
        self._number: int = api_payload['id']
        self._title: str = api_payload['title']
        self._creator: User = User(api_payload['author'])
        self._labels: list[Any] = api_payload['labels']
        self._state: str = api_payload['state']
        self._assignees: list[User] = list(map(lambda a: User(a),api_payload['assignees']))
        self._milestone: Any = api_payload['milestone']
        self._url: str = api_payload['_links']['self']
        self._repository_url: str = api_payload['_links']['project']
        self._labels_url: str = api_payload['_links']['self']
        self._comments_url: str = api_payload['_links']['notes']
        self._assignees_url: str = api_payload['_links']['self']
        self._events_url: str = api_payload['_links']['self']

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
