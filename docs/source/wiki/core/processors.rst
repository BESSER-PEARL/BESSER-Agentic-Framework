Processors
==========

The `Processor` class defines an abstract base class for processing user or agent messages within the system. It serves as a template to implement processors that can modify messages before they are handled by other components.

Overview
--------

Processors are used to define custom processing steps for messages exchanged between users and the agent. They can be applied to either user messages, agent messages, or both.

To implement a custom processor, inherit from the `Processor` class and override the `process` method.

Creating a custom Processor
---------------------------

Here is an example of how to create a custom processor that processes both user and agent messages:

.. code:: python

    from baf.core.agent import Agent
    from baf.core.session import Session
    from baf.core.processors.processor import Processor

    class MyCustomProcessor(Processor):
        def __init__(self, agent):
            super().__init__(agent=agent, user_messages=True, agent_messages=True)

        def process(self, session: 'Session', message: str) -> str:
            # Custom processing logic goes here
            processed_message = message.lower()  # Example: convert message to lowercase
            return processed_message

    # Usage
    agent = Agent('greetings_agent')
    # Initialise processor
    my_processor = MyCustomProcessor(agent)

The example demonstrates the implementation of a `MyCustomProcessor` that converts both the user's messages to the agent and the agent's responses to lowercase.

.. note::

    - A processor can also store some information in the user session, see :any:`language-detection-processor` as an example.
    - A processor can use other agent components. For instance, :doc:`LLMs <../nlp/llm>` already defined in the agent can be accessed within the processor.
      If you define a parameter `llm_name` in your processor, it could be accessed within the process method as follows:
      `llm = self.agent.nlp_engine._llms[self.llm_name]`

Methods
-------

`Processor` defines the following methods:

- **__init__(self, user_messages: bool = False, agent_messages: bool = False)**
  
  Initializes a new `Processor` instance.

Parameters:
  
  - **agent** (`Agent`): The agent the processor belongs to.
  - **user_messages** (`bool`): Whether the processor should be applied to user messages. Default is `False`.
  - **agent_messages** (`bool`): Whether the processor should be applied to agent messages. Default is `False`.

Raises:
  
  - **ProcessorTargetUndefined**: If neither `user_messages` nor `agent_messages` is set to `True`.

- **process(self, session: 'Session', message: Any) -> Any**
  
Abstract method that processes a message. This method should be overridden in subclasses to define custom processing logic.

Parameters:
  
  - **session** (`Session`): The current session object, containing the state and context of the agent-user interaction.
  - **message** (`Any`): The message to be processed.

Returns:
  
  - **Any**: The processed message. The return type can vary depending on the implementation.

.. note::

    The process method MUST return the processed message, even if no changes were applied.

Raising Exceptions
------------------

The following exceptions may be raised:

- **ProcessorTargetUndefined**: Raised if a `Processor` is created without specifying either `user_messages` or `agent_messages` as `True`.

Available processors
--------------------
This section contains a list of implemented processors.


.. _language-detection-processor:

LanguageDetectionProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`LanguageDetectionProcessor <baf.core.processors.language_detection_processor.LanguageDetectionProcessor>`
attempts to detect the language of given messages by using the `langdetect <https://pypi.org/project/langdetect/>`_ library.
When processed, the recognized language will be stored as a session variable in ISO 639-1 format and can be fetched with the following call:

.. code:: python

    session.get('detected_lang')


.. _user-adaptation-processor:

UserAdaptationProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`UserAdaptationProcessor <baf.core.processors.user_adaptation_processor.UserAdaptationProcessor>`
uses an LLM to rewrite outgoing text for a user's profile, such as their experience level
or preferred explanation style. It registers itself with the agent automatically and targets
agent messages, not incoming user messages.

First configure an LLM API key in ``config.yaml`` (see :doc:`../configuration_properties`):

.. code:: yaml

    nlp:
      openai:
        api_key: YOUR-OPENAI-API-KEY

The following example registers an LLM and uses its name in the processor. The state body
sets a profile for the current session **before the first reply**, then sends an ordinary
``session.reply()``. The WebSocket platform passes that text through the processor before
delivering it to the user.

.. code:: python

    from baf.core.agent import Agent
    from baf.core.session import Session
    from baf.core.processors.user_adaptation_processor import UserAdaptationProcessor
    from baf.nlp.llm.llm_openai_api import LLMOpenAI

    agent = Agent('adaptive_agent')
    agent.load_properties('config.yaml')
    websocket_platform = agent.use_websocket_platform(use_ui=True)
    llm = LLMOpenAI(agent=agent, name='gpt-4o-mini', parameters={})
    processor = UserAdaptationProcessor(
        agent=agent,
        llm_name=llm.name,
        context='You explain how conversational agents work.',
    )

    def introduction_body(session: Session):
        processor.add_user_model(
            session=session,
            user_model={
                'experience': 'beginner',
                'preferred_style': 'plain language with a short example',
            },
        )
        session.reply('An intent represents the goal of a user message.')

    introduction_state = agent.new_state('introduction', initial=True)
    introduction_state.set_body(introduction_body)

    if __name__ == '__main__':
        agent.run()

``llm_name`` must match a registered LLM. Profiles are stored by ``session.id`` in the
processor; they are not loaded automatically from ``Agent.user_profiles``. Initialize one
for each session before any outgoing text is processed, otherwise the current implementation
raises ``KeyError`` for the missing profile.

Call ``add_user_model()`` again to replace a session's profile. For example, a later state
body could use a different explanation style:

.. code:: python

    def advanced_explanation_body(session: Session):
        processor.add_user_model(
            session=session,
            user_model={
                'experience': 'advanced',
                'preferred_style': 'concise technical terminology',
            },
        )
        session.reply('Intent classification maps a message to an intent.')

The next reply uses the replacement profile; other sessions retain their own profiles.
These profiles live in the processor's memory, so initialize them again after a restart.
Each outgoing string processed this way makes an LLM prediction, even when the profile
has not changed. The profile and original message are included in that request. The example
requests a particular style; the exact wording still depends on the model.


API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Processor: :class:`baf.core.processors.processor.Processor`
- Processor.process(): :meth:`baf.core.processors.processor.Processor.process`
- UserAdaptationProcessor: :class:`baf.core.processors.user_adaptation_processor.UserAdaptationProcessor`
- UserAdaptationProcessor.add_user_model(): :meth:`baf.core.processors.user_adaptation_processor.UserAdaptationProcessor.add_user_model`
- Session: :class:`baf.core.session.Session`
- ProcessorTargetUndefined: :class:`baf.exceptions.exceptions.ProcessorTargetUndefined`
