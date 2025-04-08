GitLab platform
===============

The GitLab Platform allows an agent to receive events from
`GitLab's webhooks <https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html>`_
and perform actions on repositories through the
`GitLab API <https://docs.gitlab.com/ee/api/rest>`_.

Our GitLab Platform uses the `gidgetlab <https://gitlab.com/beenje/gidgetlab>`_
library, which is an asynchronous GitLab API wrapper for Python.

.. note::

    There are some properties the agent needs in order to properly set GitLab and webhook connections. More details in
    the :any:`configuration properties <properties-gitlab_platform>` documentation.


How to use it
-------------

After you instantiate your agent, simply call the following function:

.. code:: python

    agent = Agent('example_agent')
    ...
    gitlab_platform = agent.use_gitlab_platform()

After that, you can use the different :any:`events sent by GitLab <gitlab-events>` to trigger transitions in your agent.

.. code:: python

    # Importing the events
    from besser.agent.platforms.gitlab.gitlab_webhooks_events import MergeRequestOpened, IssuesOpened, WikiPageCreated, Push

    # Merge Request
    idle.when_event(MergeRequestOpened()).go_to(merge_state)
    # Issues
    idle.when_event(IssuesOpened()).go_to(issue_state)
    # Wiki Pages
    idle.when_event(WikiPageCreated()).go_to(wiki_state)
    # Push
    idle.when_event(Push()).go_to(push_state)


.. note::

    The agent needs to provide a public URL to receive the webhooks.
    For local testing you can use `ngrok <https://ngrok.com/docs/getting-started/>`_.


In addition to webhooks events, the gitlab platform offers:

- Access to the payload of the received event
- Wrapper classes on top of the issues and users payload
- Methods to open, get, comment, label and assign a user to an issue

These abstractions allows to receive webhooks events and perform agent actions on the repository as a reaction.
The following example wait for issues opening events to add a thanking message as comment:

.. code:: python

    # How to import the Issue class
    from besser.agent.platforms.gitlab.gitlab_objects import Issue

    def issue_body(session: Session):
        # Access through the Session to the IssuesOpened GitLabEvent that triggered the transition
        event: GitLabEvent = session.event
        # Extract useful information
        user_repo = event.payload['project']['path_with_namespace'].split('/')
        issue_iid = event.payload['object_attributes']['iid']
        # Get the issue as object
        issue: Issue = gitlab_platform.get_issue(
            user=user_repo[0],
            repository=user_repo[1],
            issue_number=issue_iid)
        # Add a thanking message to the opened issue
        gitlab_platform.comment_issue(issue,
            'Hey,\n\nThanks for opening an issue!<br>We will look at that as soon as possible.')


⏳ We are working on providing abstractions for more concepts than issues, so stay tuned!


Gitgetlab Wrapper
-----------------

The BAF GitLab Platform wraps some functionalities of the gidgetlab library (such as handling webhooks or
act on issues), but not all of them.

In order to use other features not included in BAF yet, we included a `__getattr__` function in the GitLabPlatform
class. It forwards the method calls not implemented in GitLabPlatform to the underlying GitLabAPI
(`gidgetlab.aiohttp.GitLabAPI <https://gidgetlab.readthedocs.io/en/latest/aiohttp.html#gidgetlab.aiohttp.GitLabAPI>`_
class, which is an extension of the abstract
`gidgetlab.abc.GitLabAPI <https://gidgetlab.readthedocs.io/en/latest/abc.html#gidgetlab.abc.GitLabAPI>`_ class).

**That means you can call any function from the GitLabPlatform as you would do in the GitLabAPI!**

Let's see an example.

You could use `getitem <https://gidgetlab.readthedocs.io/en/latest/abc.html#gidgetlab.abc.GitLabAPI.getitem>`_
to get the list of contributors to a repository. Since this is not integrated in our GitLabPlatform,
you can simply call it and it will be forwarded:

.. code:: python

    def example_body(session: Session):
        payload = gitlab_platform.getitem(f'/projects/NAMESPACE%2FPROJECT_PATH/repository/contributors')

.. note::

    Here we use the `Namespaced path <https://docs.gitlab.com/ee/api/rest/index.html#namespaced-paths>`_
    notation (i.e. "NAMESPACE%2FPROJECT_PATH") for the project, but using project id works too.

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.use_gitlab_platform(): :meth:`besser.agent.core.agent.Agent.use_gitlab_platform`
- GitLabEvent: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.GitLabEvent`
- GitLabPlatform: :class:`besser.agent.platforms.gitlab.gitlab_platform.GitLabPlatform`
- GitLabPlatform.comment_issue(): :meth:`besser.agent.platforms.gitlab.gitlab_platform.GitLabPlatform.comment_issue`
- GitLabPlatform.get_issue(): :meth:`besser.agent.platforms.gitlab.gitlab_platform.GitLabPlatform.get_issue`
- Issue: :meth:`besser.agent.platforms.gitlab.gitlab_objects.Issue`
- IssuesOpened: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.IssuesOpened`
- MergeRequestOpened: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.MergeRequestOpened`
- Push: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.Push`
- WikiPageCreated: :meth:`besser.agent.library.transition.events.gitlab_webhooks_events.WikiPageCreated`
