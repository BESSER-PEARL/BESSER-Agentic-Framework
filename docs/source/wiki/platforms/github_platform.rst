GitHub platform
===============

The GitHub Platform allows an agent to receive events from
`GitHub's webhooks <https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks>`_
and perform actions on repositories through the
`GitHub API <https://docs.github.com/en/rest>`_.

Our GitHub Platform uses the `gidgethub <https://github.com/gidgethub/gidgethub>`_
library, which is an asynchronous GitHub API wrapper for Python.

.. note::

    There are some properties the agent needs in order to properly set GitHub and webhook connections. More details in
    the :any:`configuration properties <properties-github_platform>` documentation.

How to use it
-------------

After you instantiate your agent, simply call the following function:

.. code:: python

    agent = Agent('example_agent')
    ...
    github_platform = agent.use_github_platform()

After that, you can use the different :any:`events sent by GitHub <github-events>` to trigger transitions in your agent.

.. code:: python

    # Pull Request
    idle.when_event(PullRequestOpened()).go_to(pull_state)
    # Issues
    idle.when_event(IssuesOpened()).go_to(issue_state)
    # Labels
    idle.when_event(LabelCreated()).go_to(label_state)
    # Stars
    idle.when_event(StarCreated()).go_to(star_state)


.. note::

    The agent needs to provide a public URL to receive the webhooks.
    For local testing you can use `ngrok <https://ngrok.com/docs/getting-started/>`_

In addition to webhooks events, the github platform offers:

- Access to the payload of the received event
- Wrapper classes on top of the issues and users payload
- Methods to open, get, comment, label and assign a user to an issue

These abstractions allows to receive webhooks events and perform agent actions on the repository as a reaction.
The following example wait for issues to open to add a thanking message as comment:

.. code:: python

    # How to import the Issue class
    from besser.agent.platforms.github.github_objects import Issue

    def issue_body(session: Session):
        # Access through the Session to the IssuesOpened GitHubEvent that triggered the transition
        event: GitHubEvent = session.event
        # Wrap the issue object of the payload in our abstraction
        issue = Issue(event.payload['issue'])
        # Add a thanking message to the opened issue
        github_platform.comment_issue(issue
            f'Hey,\n\nThanks for opening an issue {issue.creator.login}!<br>We will look at that as soon as possible.')


⏳ We are working on providing abstractions for more concepts than issues, so stay tuned!


Gidgethub Wrapper
-----------------

The BAF GitHub Platform wraps some functionalities of the gidgethub library (such as handling webhooks or
act on issues), but not all of them.

In order to use other features not included in BAF yet, we included a `__getattr__` function in the GitHubPlatform
class. It forwards the method calls not implemented in GitHubPlatform to the underlying GitHubAPI
(`gidgethub.aiohttp.GitHubAPI <https://gidgethub.readthedocs.io/en/latest/aiohttp.html#gidgethub.aiohttp.GitHubAPI>`_
class, which is an extension of the abstract
`gidgethub.abc.GitHubAPI <https://gidgethub.readthedocs.io/en/latest/abc.html#gidgethub.abc.GitHubAPI>`_ class).

**That means you can call any function from the GitHubPlatform as you would do in the GitHubAPI!**

Let's see an example.

You could use `getitem <https://gidgethub.readthedocs.io/en/latest/abc.html#gidgethub.abc.GitHubAPI.getitem>`_
to get the list of contributors to a repository. Since this is not integrated in our GitHubPlatform,
you can simply call it and it will be forwarded:

.. code:: python

    def example_body(session: Session):
        payload = github_platform.getitem(f'/repos/OWNER/REPO/contributors')

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.use_github_platform(): :meth:`besser.agent.core.agent.Agent.use_github_platform`
- GitHubEvent: :meth:`besser.agent.library.transition.events.github_webhooks_events.GitHubEvent`
- GitHubPlatform: :class:`besser.agent.platforms.github.github_platform.GitHubPlatform`
- GitHubPlatform.comment_issue(): :meth:`besser.agent.platforms.github.github_platform.GitHubPlatform.comment_issue`
- Issue: :meth:`besser.agent.platforms.github.github_objects.Issue`
- IssuesOpened: :meth:`besser.agent.library.transition.events.github_webhooks_events.IssuesOpened`
- LabelCreated: :meth:`besser.agent.library.transition.events.github_webhooks_events.LabelCreated`
- PullRequestOpened: :meth:`besser.agent.library.transition.events.github_webhooks_events.PullRequestOpened`
- StarCreated: :meth:`besser.agent.library.transition.events.github_webhooks_events.StarCreated`
- User: :meth:`besser.agent.platforms.github.github_objects.User`
