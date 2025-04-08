from datetime import datetime
from typing import Any

from besser.agent.core.transition.event import Event


class GitLabEvent(Event):
    """Base GitLab event.

    Args:
        category (str): the event category
        action (str): the event action
        payload (Any): the event payload

    Attributes:
        _category (str): the event category
        _action (str): the event action
        _payload (Any): the event payload
    """

    def __init__(self, category: str, action: str, payload: Any):
        super().__init__(name=category + action, timestamp=datetime.now())
        self._category: str = category
        self._action: str = action
        self._payload = payload

    @property
    def action(self):
        """str: The action of the event"""
        return self._action

    @property
    def payload(self):
        """Any: The payload of the event"""
        return self._payload

    def is_matching(self, event: 'Event') -> bool:
        """Check whether a GitLab event matches another one.

        Args:
            event (Event): the target event to compare

        Returns:
            bool: true if both events match, false otherwise
        """
        if isinstance(event, GitLabEvent):
            return self._category == event._category and self._action == event._action
        return False


class IssuesClosed(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Issue Hook', 'close', payload)


class IssuesUpdated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Issue Hook', 'update', payload)


class IssuesOpened(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Issue Hook', 'open', payload)


class IssuesReopened(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Issue Hook', 'reopen', payload)


class IssueCommentCreated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('IssueNote Hook', 'create', payload)


class IssueCommentUpdated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('IssueNote Hook', 'update', payload)


class MergeRequestClosed(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'close', payload)


class MergeRequestUpdated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'update', payload)


class MergeRequestOpened(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'open', payload)


class MergeRequestReopened(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'reopen', payload)


class MergeRequestApproved(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'approved', payload)


class MergeRequestUnapproved(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'unapproved', payload)


class MergeRequestApproval(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'approval', payload)


class MergeRequestUnapproval(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'unapproval', payload)


class MergeRequestMerge(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Merge Request Hook', 'merge', payload)


class MergeRequestCommentCreated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('MergeRequestNote Hook', 'create', payload)


class MergeRequestCommentUpdated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('MergeRequestNote Hook', 'update', payload)


class WikiPageCreated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Wiki Page Hook', 'create', payload)


class WikiPageUpdated(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Wiki Page Hook', 'update', payload)


class WikiPageDeleted(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Wiki Page Hook', 'delete', payload)


class Push(GitLabEvent):
    def __init__(self, payload=None):
        super().__init__('Push Hook', '', payload)
