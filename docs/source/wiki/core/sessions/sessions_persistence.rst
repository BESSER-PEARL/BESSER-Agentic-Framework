Persisting sessions across restarts
====================================

It is possible to persist user sessions across agent restarts so that sessions are not lost. 
To enable this feature, you first need to have the :doc:`monitoring database <../db/monitoring_db>` running and configured in your agent.
Secondly, the used platform needs to support user persistence by providing a way for users to authenticate themselves and follow the correct protocol for persistence (as defined in :doc:`../platforms`).
When the agent boots it reloads the last known state, chat history, and any
session variables you stored via ``Session.set``. As a result:

* Users stay in the same conversational state after the restart (don't start at the initial state).
* Session variables are not lost and remain available
	through ``Session.get``.
* The chat history is rehydrated, allowing UI clients to display past messages
	immediately after reconnecting (this needs to be implemented on the platform's side).

Each platform expects different configuration for user persistence. For example, the WebSocket platform requires setting ``persist_users=True`` when initializing it whereas the Telegram platform has persistence enabled by default if the :doc:`monitoring database <../db/monitoring_db>` is running.


