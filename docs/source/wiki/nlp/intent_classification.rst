Intent classification
=====================

When a user sends a message to the agent, it needs to recognize its intention among a set of :doc:`intents <../core/intents>`.
In NLP, this problem is known as Text Classification.

    Given an user message, the agent must classify it into one of the possible intents.

To successfully do this, it is necessary to provide a set of example sentences for each intent
(this is the training data).

In this section, we delve into the different intent classifiers available in BAF. Each one has its pros and cons.

**Each agent state has its own intent classifier.** This is because each intent classifier is trained to recognize only those
intents allowed in its state. This way, you can choose the intent classifier that better suits for each state depending
on the needs. Let's see how to configure this.

.. _intent-classifier-configuration:

Configuration
-------------

Each state has an :doc:`intent classifier configuration <../../api/nlp/intent_classifier_configuration>`.
that defines its intent classifier's properties.

This is how you can create an intent classifier configuration:

.. code:: python

    from baf.nlp.intent_classifier.intent_classifier_configuration import SimpleIntentClassifierConfiguration

    agent = Agent('example_agent')

    simple_config = SimpleIntentClassifierConfiguration(
        framework='pytorch',
        activation_last_layer='sigmoid',
        lr=0.001
    )

We can set a configuration for a specific state:

.. code:: python

    example_state = agent.new_state('example_state', ic_config=simple_config)

Or a default configuration for all states (note that this would replace any previously defined configuration):

.. code:: python

    agent.set_default_ic_config(simple_config)

.. note::

    If you don't specify any configuration for a state, the :any:`simple-intent-classifier` (PyTorch implementation)
    will be selected by default.

.. note::

    All intent classifier configuration classes implement the :class:`~baf.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration` class
    and all intent classifiers implement the :class:`~baf.nlp.intent_classifier.intent_classifier.IntentClassifier` class


.. _simple-intent-classifier:

Simple Intent Classifier
------------------------

The Simple Intent Classifier is based on a basic neural network as the prediction model. It is trained with the intent's
training sentences. When running, it is able to predict the intent of a message if it is close to any of the training
sentences.

We provide 2 implementations of the same intent classifier:

- :class:`~baf.nlp.intent_classifier.simple_intent_classifier_pytorch.SimpleIntentClassifierTorch`:
  PyTorch-based implementation. It uses a `PyTorch module <https://pytorch.org/docs/stable/generated/torch.nn.Module>`_
  as the prediction model.

- :class:`~baf.nlp.intent_classifier.simple_intent_classifier_tensorflow.SimpleIntentClassifierTF`:
  Tensorflow-based implementation. It uses a `Keras <https://keras.io/>`_ neural network as the prediction model.

.. note::

    Even though both intent classifiers implement the same neural network architecture, the performance may not be equal.

    Also, the training process is not deterministic and performance may vary between different agent executions.

    The neural network architecture can be customized.

The Simple Intent Classifier is based on a basic
neural network as the prediction model. It is trained with the intent's training sentences.
When running, it is able to predict the intent of a message if it is close to any of the training sentences.

You can see all the configuration possibilities of this intent classifier here (including the framework selection):
:class:`~baf.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`

The :obj:`~baf.nlp.NLP_PRE_PROCESSING` agent property influences the performance of this intent classifier. If you
decide to preprocess the user messages (this is done before the intent prediction), the intent predictions will
probably be more accurate.

When to use it?
~~~~~~~~~~~~~~~

- If you want a very light, customizable and quickly trainable intent classifier.
- If you are certain of how the user messages will look like.
- If you want to restrict the user's writing freedom, forcing him/her to write in a particular way or to choose from a
  predefined set of messages (with buttons).

Pros
~~~~

- Free
- Fast training
- Fast predictions
- Very small

Cons
~~~~

- You need to provide training sentences (quantity and quality increases the success probabilities)
- Not possible to understand semantic similarities, only word similarities. For example, if a training sentence is 'yes'
  and the user says 'of course' (something not present in the training sentences), the prediction will fail.
- If 2 or more intents have very similar training sentences, probabilities of wrong predictions increase

Example scenario
~~~~~~~~~~~~~~~~

Imagine your agent has a state where it asks some question to the user, expecting a yes/no answer:

.. code:: python

    yes_intent = agent.new_intent('yes_intent', ['Yes'])

    no_intent = agent.new_intent('no_intent', ['No'])

    example_state = agent.new_state('example_state', ic_config=SimpleIntentClassifierConfiguration())

    def example_body(session: Session):
        websocket_platform.reply(session, 'Do you want to continue talking?')
        websocket_platform.reply_options(session, ['Yes', 'No'])

    example_state.set_body(example_body)
    example_state.when_intent_matched(yes_intent).go_to(state1)
    example_state.when_intent_matched(no_intent).go_to(state2)

In this kind of situations, the Simple Intent Classifier will satisfy the agent needs. You can also remove the
reply_options message and let the user write, although if you want to force the user reply, this is strongly recommended.


.. _llm-intent-classifier:

LLM Intent Classifier
---------------------

The :class:`~baf.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier` uses a :doc:`Large Language Model
(LLM) <llm>` to predict the intent of a message. LLMs are multimodal models that can solve a wide variety of tasks just by
providing them the right prompts in natural language. In this case, we can ask them to classify a sentence into the
appropriate intent.

You can see all the configuration possibilities of this intent classifier here:
:class:`~baf.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`

When to use it?
~~~~~~~~~~~~~~~

- If you want a powerful and very smart intent classifier.
- If you don't quite know how the user messages will look like.
- If you want to give the users writing freedom.

Pros
~~~~

- No need to train it. It is a general purpose model.
- Through API, no need to host it (also possible to run it locally with HuggingFace)
- No need for training sentences, just intent descriptions (you can also use both).
- Understands semantic similarities. For example, if a training sentence is 'yes' and the user says 'of course'
  (something not present in the training sentences), the prediction will probably hit.
- You can select any LLM you want (even different LLMs for each state)
- Powerful Named Entity Recognition integrated.

Cons
~~~~

- APIs not free to use
- LLMs are big (this can only affect you if you run them locally)
- Some predictions may be slow (a few seconds)

Example scenario
~~~~~~~~~~~~~~~~

Imagine your agent has a state where some of the possible intents is a 'help' intent, intended to guide the
user on how to use the agent. Since there are a lot of different ways the user could ask for help, and we don't
want to think about them all, we can simply provide an intent description and use the LLM Intent Classifier:

.. code:: python

    from baf.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
    from baf.nlp.llm.llm_openai_api import LLMOpenAI

    agent = Agent('example_agent')
    llm = LLMOpenAI(agent=agent, name='gpt-4o-mini')

    ic_config = LLMIntentClassifierConfiguration(
        llm_name='gpt-4o-mini',
        parameters={
            "seed": None,
            "top_p": 1,
            "temperature": 1,
        },
        use_intent_descriptions=True,
        use_training_sentences=False,
        use_entity_descriptions=True,
        use_entity_synonyms=False
    )

    help_intent = agent.new_intent(
        name='help_intent',
        description='The user needs help to be able to use the agent properly or to find some information'
    )

    example_state = agent.new_state('example_state', ic_config=ic_config)

    def example_body(session: Session):
        # ...

    example_state.set_body(example_body)
    example_state.when_intent_matched(intent1).go_to(state1)
    # ...
    example_state.when_intent_matched(help_intent).go_to(help_state)


.. _jev-intent-classifier:

Jev Intent Classifier
---------------------

The :class:`~baf.nlp.intent_classifier.jev_intent_classifier.JevIntentClassifier` uses :doc:`Jev <jev>`, TypeSafe AI's
typed decision model. It asks Jev a single *Choice* question whose options are the state's intents, each described by
its description and some of its training sentences. Jev returns a calibrated probability for each intent, which becomes
the intent score (and is compared with the :obj:`~baf.nlp.NLP_INTENT_THRESHOLD`).

By default, an extra *none of the above* option is added. When the message matches none of the intents, Jev gives most
of the probability to that option, so no intent passes the threshold and the agent falls back.

Jev only chooses the intent: it does not extract the intent parameters. They are filled by the agent's
:doc:`NER <ner>` (you can disable this with ``use_ner=False``).

You can see all the configuration possibilities of this intent classifier here:
:class:`~baf.nlp.intent_classifier.intent_classifier_configuration.JevIntentClassifierConfiguration`

When to use it?
~~~~~~~~~~~~~~~

- If you want an intent classifier that understands the meaning of the messages, like the LLM Intent Classifier, but
  faster and cheaper.
- If you want scores you can rely on as probabilities to set thresholds.

Pros
~~~~

- No need to train it. Intent descriptions are enough (you can also use training sentences as examples).
- Understands semantic similarities.
- Calibrated probabilities (TypeSafe calibrates them so that, for instance, 0.9 means right about 9 times out of 10).
- Fast (around 100-300 ms per prediction) and cheap (you pay for input tokens only).

Cons
~~~~

- API not free to use (and needs network access).
- No parameter extraction (the agent's NER is used instead).
- A state can have at most 31 intents (Jev Choice questions accept up to 32 options, including the *none* option).

Example scenario
~~~~~~~~~~~~~~~~

.. code:: python

    from baf.nlp.intent_classifier.intent_classifier_configuration import JevIntentClassifierConfiguration
    from baf.nlp.jev.jev import Jev

    agent = Agent('example_agent')
    agent.load_properties('config.yaml')  # with nlp.typesafe.api_key
    jev = Jev(agent=agent, model='jev-latest')

    ic_config = JevIntentClassifierConfiguration(
        use_intent_descriptions=True,
        use_training_sentences=True,
        max_training_sentences=5,
        none_option=True
    )

    help_intent = agent.new_intent(
        name='help_intent',
        description='The user needs help to be able to use the agent properly or to find some information'
    )

    example_state = agent.new_state('example_state', ic_config=ic_config)
    example_state.when_intent_matched(help_intent).go_to(help_state)

.. note::

    If a state uses the Jev Intent Classifier and you did not create a :class:`~baf.nlp.jev.jev.Jev` client, a default
    one (model ``jev-latest``) is created when the agent starts.

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.new_intent(): :meth:`baf.core.agent.Agent.new_intent`
- Agent.new_state(): :meth:`baf.core.agent.Agent.new_state`
- Agent.set_default_ic_config(): :meth:`baf.core.agent.Agent.set_default_ic_config`
- Intent: :class:`baf.core.intent.intent.Intent`
- IntentClassifierConfiguration: :class:`baf.nlp.intent_classifier.intent_classifier_configuration.IntentClassifierConfiguration`
- Jev: :class:`baf.nlp.jev.jev.Jev`
- JevIntentClassifier: :class:`baf.nlp.intent_classifier.jev_intent_classifier.JevIntentClassifier`
- JevIntentClassifierConfiguration: :class:`baf.nlp.intent_classifier.intent_classifier_configuration.JevIntentClassifierConfiguration`
- LLMIntentClassifierConfiguration: :class:`baf.nlp.intent_classifier.intent_classifier_configuration.LLMIntentClassifierConfiguration`
- LLMOpenAI: :class:`baf.nlp.llm.llm_openai_api.LLMIntentClassifierConfiguration`
- Session: :class:`baf.core.session.Session`
- SimpleIntentClassifierConfiguration: :class:`baf.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`
- SimpleIntentClassifierTF: :class:`baf.nlp.intent_classifier.simple_intent_classifier_tensorflow.SimpleIntentClassifierTF`
- SimpleIntentClassifierTorch: :class:`baf.nlp.intent_classifier.simple_intent_classifier_pytorch.SimpleIntentClassifierTorch`
- State: :class:`baf.core.state.State`
- State.set_body(): :meth:`baf.core.state.State.set_body`
- State.when_intent_matched(): :meth:`baf.core.state.State.when_intent_matched`
- TransitionBuilder.go_to(): :meth:`baf.core.transition.transition_builder.TransitionBuilder.go_to`
