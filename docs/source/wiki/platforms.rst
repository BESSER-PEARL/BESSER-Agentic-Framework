Platforms
=========

An agent has to interact with the users through some communication channel. BAF's platforms wrap all the
necessary code to build the connection between the agent and a communication channel.

All platforms implement the abstract class :class:`~besser.agent.platforms.platform.Platform`. It defines the methods any
platform must have. So, if you would like to create your own platform (and contribute to the BAF
development 🙂), it must implement them according to the platform needs:

- :meth:`~besser.agent.platforms.platform.Platform.initialize`: Initialize the platform. It is called internally when
  you run the agent (:meth:`Agent.run() <besser.agent.core.agent.Agent.run>`). You may need to set some things previously to the
  platform execution.

- :meth:`~besser.agent.platforms.platform.Platform.start`: Start the platform execution. It is called internally when
  you run the agent (:meth:`Agent.run() <besser.agent.core.agent.Agent.run>`).

- :meth:`~besser.agent.platforms.platform.Platform.stop`: Stop the platform. It is called internally when
  you stop the agent (:meth:`Agent.stop() <besser.agent.core.agent.Agent.stop>`).

- :meth:`~besser.agent.platforms.platform.Platform._send`: Send a payload (usually a message) to the user. This is a
  private method. It is called internally by other platform methods, such as the following one.

- :meth:`~besser.agent.platforms.platform.Platform.reply`: Send a textual message to the user.

Additionally, a platform could have specific methods for it, as you can see in our implemented platforms.

Session persistence
-------------------

BAF already persists user sessions at the backend level, so restarting an agent
brings every user back to the last state with their stored parameters intact.
However, the client UI must authenticate the user so the platform can map the
incoming connection to the correct session.

* **Telegram** ships with its own user identity, so persistence works out of the
  box as soon as you configure the Telegram platform. See :doc:`platforms/telegram_platform`
  for setup details.
* **WebSocket + Streamlit UI** includes a built-in login page that tags each
  browser session with a username before opening the socket. Learn how to enable
  persistence in :doc:`platforms/websocket_platform`.
* **Custom WebSocket interfaces** must implement the same identification
  protocol (authenticate the user and include the user identifier in each
  message) so the agent can reuse the persisted session. Follow the guidelines
  in :doc:`platforms/websocket_platform` if you plan to build your own frontend
  on top of the WebSocket API.

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   platforms/websocket_platform
   platforms/telegram_platform
   platforms/github_platform
   platforms/gitlab_platform
