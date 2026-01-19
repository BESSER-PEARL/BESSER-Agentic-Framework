Persisting sessions across restarts
====================================

It is possible to persist user sessions across agent restarts so that sessions are not lost. 
To enable this feature, you first need to have the :doc:`monitoring database <../../db/monitoring_db>` running and configured in your agent.
Secondly, you need to set the ``persist_sessions=True`` parameter when initializing the agent:

.. code:: python

	agent = Agent('greetings_agent', persist_sessions=True)  # set persist_sessions=True to enable session persistence across restarts


Finally, the used platform needs to support user persistence by providing a way for users to authenticate themselves and follow the correct protocol for persistence (as defined in :doc:`../../platforms`).
As a result, when the agent boots it:

* Restores the last known state, meaning that users stay in the same conversational state after the restart (don't start at the initial state).
* Session variables set through ``Session.set`` are not lost and remain available
	through ``Session.get``.


As a reminder, BAF takes care of the logic to restore sessions, but the platform is responsible for identifying users correctly.
Thus, depending on the platform you are using, you need to set the correct configuration to enable user authentication (more on that in :doc:`../../platforms`).


