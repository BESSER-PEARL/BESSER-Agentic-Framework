Events
======

An agent can receive :class:`events <besser.agent.core.transition.event.Event>` through its platforms.

An agent can define transitions from one state to another based on the reception of specific events.

.. note::

    The :doc:`transitions` wiki page explains how to define event-based transitions in agents.

All events contain the following information:

- **name**: name of the event
- **session_id**: the id of the session the event was sent to. If an event has been broadcasted to all agent sessions, this attribute is empty
- **timestamp**: the timestamp indicating the event reception instant

Then, **each event implementation may have different attributes**.

You can access the received event from the user session (i.e., from :any:`state bodies<state-body>` or :any:`transition conditions<transition-conditions>`)

The session always contains the last received event (the one that triggered the transition to the state you are reading the event from)

.. code:: python

    def example_body(session: Session):
        event: Event = session.event
        # Depending on the type of event, we can access specific information
        if isinstance(event, ReceiveTextEvent):
            message: str = event.message
            intent_prediction: IntentClassifierPrediction = event.predicted_intent
            human: bool = event.human  # Whether the message was sent by a human or not
        if isinstance(event, ReceiveFileEvent):
            file: File = event.file
            human: bool = event.human
        if isinstance(event, GitHubEvent) or isinstance(event, GitLabEvent):
            category = event.category
            action = event.action
            payload = event.payload

Next, we introduce all available events in BAF.

.. _base-events:

Base events
-----------

This set of events are used to receive data, usually in the form of text, JSON or file messages.

Currently, :doc:`../platforms/websocket_platform` and :doc:`../platforms/telegram_platform` use these events to
send data to the agents.

For example, when a user sends a text message to an agent through the WebSocket platform, the platform packs it in a
ReceiveTextEvent so the agent can use it to trigger the appropriate transition to another state.

.. important::

    All events described in :doc:`../../api/library/base_events` API documentation.

.. _github-events:

GitHub events
-------------

You can use the :doc:`../platforms/github_platform` in an agent to receive events from GitHub.

.. important::

    All events described in :doc:`../../api/library/github_webhooks_events` API documentation.


.. _gitlab-events:

GitLab events
-------------

You can use the :doc:`../platforms/gitlab_platform` in an agent to receive events from GitLab.

.. important::

    All events described in :doc:`../../api/library/gitlab_webhooks_events` API documentation.

API References
--------------

- Event: :class:`besser.agent.core.transition.event.Event`
- GitHubEvent: :meth:`besser.agent.library.transition.events.github_webhooks_events.GitHubEvent`
- GitLabEvent: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.GitLabEvent`
- IntentClassifierPrediction: :class:`besser.agent.nlp.intent_classifier.intent_classifier_prediction.IntentClassifierPrediction`
- ReceiveFileEvent: :class:`besser.agent.library.transition.events.base_events.ReceiveFileEvent`
- ReceiveTextEvent: :class:`besser.agent.library.transition.events.base_events.ReceiveTextEvent`
- Session: :class:`besser.agent.core.session.Session`
