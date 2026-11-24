Jev
===

`Jev <https://docs.typesafe.ai>`_ is TypeSafe AI's typed decision model. Instead of generating free text like an
:doc:`LLM <llm>`, it answers typed questions about a piece of text (the *state*) and returns **calibrated
probabilities**:

- **Noul**: a yes/no question. The answer is the probability that the condition is true (e.g., 0.93).
- **Choice**: pick one option out of a set. The answer is the winning option, a probability per option and a confidence.
- **Score**: place the state on an ordered scale. The answer is the expected level, a probability per level and a
  confidence.

This makes Jev a good fit for the decisions an agent takes all the time: which intent the user has, whether a message
needs a human, how urgent a request is... You can use the probabilities as thresholds in your agent logic.

You can also check the :doc:`../../examples/jev_agent` for a complete example.

Setup
-----

Create an API key at `console.typesafe.ai <https://console.typesafe.ai>`_ and set it in the
:obj:`~baf.nlp.TYPESAFE_API_KEY` agent property (``nlp.typesafe.api_key``), for instance in your configuration file:

.. code:: yaml

    nlp:
      typesafe:
        api_key: YOUR-API-KEY

Then create the Jev client:

.. code:: python

    from baf.core.agent import Agent
    from baf.nlp.jev.jev import Jev

    agent = Agent('example_agent')
    agent.load_properties('config.yaml')

    jev = Jev(agent=agent, model='jev-latest')

.. note::

    ``jev-latest`` always points to the newest stable model. If you tune thresholds on Jev's probabilities, pin a
    version (e.g., ``model='jev-1.13.0'``) so they do not shift when a new model is released.

Asking questions
----------------

You can ask several questions over the same state in one request. Each question has an id of your choice, and the
answers come back under the same ids:

.. code:: python

    from baf.nlp.jev.jev import Noul, Choice, Score

    def ticket_body(session: Session):
        response = jev.ask(session.event.message, {
            'refund': Noul('Does the message ask for a refund?'),
            'department': Choice('Which department should handle this ticket?', {
                'billing': 'Payments, invoices, refunds',
                'technical': 'Bugs, crashes, login problems',
                'sales': None,  # None if the option name explains itself
            }),
            'urgency': Score('How urgent is this ticket?', [
                'Can wait a week',            # level 0
                'Needs an answer this week',  # level 1
                'Needs an answer today',      # level 2
            ]),
        })
        if response['refund'].noul > 0.8:
            ...
        department = response['department'].choice               # e.g. 'billing'
        probabilities = response['department'].probabilities      # e.g. {'billing': 0.88, 'technical': 0.12, ...}
        urgency = response['urgency'].score                       # e.g. 1.05 (expected level)

The state can be a string, a dict or a list, so you can pass more context than the message:

.. code:: python

    jev.ask({'message': session.event.message, 'previous_order': order}, questions)

For a single question, use the shortcuts:

.. code:: python

    probability = jev.noul(message, 'Does the user want to talk to a human?')
    answer = jev.choice(message, 'Which language is the message written in?', ['en', 'fr', 'de'])
    answer = jev.score(message, 'How angry is the user?', ['Calm', 'Annoyed', 'Very angry'])

Each answer is a :class:`~baf.nlp.jev.jev.JevAnswer` with these fields:

- ``noul``: for Noul questions, the probability that the condition is true. Noul answers have no ``confidence``: the
  probability is the confidence.
- ``choice``, ``probabilities``, ``confidence``: for Choice questions.
- ``score``, ``probabilities``, ``legend``, ``confidence``: for Score questions. Levels are ints (0, 1, 2...).

The response also tells you which exact model answered (``response.model``, e.g. ``jev-1.13.0``) and the token usage
(``response.usage``).

If a request fails, a :class:`~baf.nlp.jev.jev.JevError` is raised (with the HTTP ``status`` and ``body``). Rate limits
(429), overload (529), timeouts and server errors are retried automatically (``max_retries``, 2 by default).

Intent classification with Jev
------------------------------

Jev can also be your agent's intent classifier. See :ref:`jev-intent-classifier`.

Gateways
--------

Jev is also served by other gateways (e.g., OpenRouter, Vercel AI Gateway, a LiteLLM proxy). To use one, set the
endpoint and the gateway's model id, and pass the gateway's API key:

.. code:: python

    jev = Jev(
        agent=agent,
        base_url='http://localhost:4000',      # your LiteLLM proxy
        path='/typesafe/v1/systemone',
        model='jev-latest',
        api_key='YOUR-GATEWAY-KEY',
    )

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.load_properties(): :meth:`baf.core.agent.Agent.load_properties`
- Jev: :class:`baf.nlp.jev.jev.Jev`
- Jev.ask(): :meth:`baf.nlp.jev.jev.Jev.ask`
- JevAnswer: :class:`baf.nlp.jev.jev.JevAnswer`
- JevError: :class:`baf.nlp.jev.jev.JevError`
- JevResponse: :class:`baf.nlp.jev.jev.JevResponse`
- Noul: :class:`baf.nlp.jev.jev.Noul`
- Choice: :class:`baf.nlp.jev.jev.Choice`
- Score: :class:`baf.nlp.jev.jev.Score`
