Entities
========

Entities are used to specify the type of information to extract from user inputs. These entities are embedded in
intent parameters.

Custom entities
---------------

Let's see how to create your own entities for your agent.

.. code:: python

    agent = Agent('weather_agent')
    ...
    city_entity = agent.new_entity('city_entity', entries={
        'Barcelona': ['BCN', 'barna'],
        'Luxembourg': ['LUX'],
    })

Entities have a set of **entries**. Each entity entry is composed by a **value** (e.g. 'Barcelona') and a list of
(optional) **synonyms** of the value (useful for values that can be called in different ways, but refer to the same
concept). In this example entity, you could add all the cities you want the agent to be able to recognise. In a real use
case, you could also get a complete list of cities in a country and create an entity with that entries.

In :any:`intents-with-parameters`, we explain how to embed entities in intent parameters.

Entity descriptions
-------------------

If you want to use the :any:`llm-intent-classifier`, you can create an entity without values. Instead, you
just would need to provide a description for that entity, although you can still add values to it. This is
an example intent with a description:

.. code:: python

    email_entity = agent.new_entity(
        name='email_entity',
        description='An entity containing email addresses',
    )

In this example, the LLM Intent Classifier will be able to recognize and extract email addresses from user messages.

.. _base-entities:

Base entities
-------------

In BESSER Agentic Framework, we include a set of predefined entities that can be used in any intent parameter like custom entities.
The difference is that you don't need to define them. We do it for you!

The following list describes all currently implemented base entities:

.. csv-table::
    :file: base_entities.csv
    :header-rows: 1

Let's see how to use base entities with an example:

.. code:: python

    from baf.library.entity.base_entities import number_entity
    ...
    agent.add_entity(number_entity)

    age_intent = agent.new_intent('age_intent', [
        'I am NUM years old',
        'My age is NUM
    ])
    age_intent.parameter('age', 'NUM', number_entity)
    ...
    def age_body(session: Session):
        event: ReceiveTextEvent = session.event
        prediction: IntentClassifierPrediction = event.predicted_intent
        age = predicted_intent.get_parameter('age').value
        session.set('age', age) # Save the age in the user session
        session.reply('Thanks for the information')
    ...

Reading date-time parameters
----------------------------

The built-in NER returns a :class:`~baf.nlp.ner.matched_parameter.MatchedParameter` for a
``datetime_entity`` parameter. Its ``value`` is a normalized ISO 8601 **string**, not a Python
``datetime`` object. Its ``info`` dictionary contains:

- ``frag``: the original date/time fragment from the user's message, before normalization
  (for example, ``tomorrow``).
- ``year``, ``month``, ``day``, ``hour``, ``minute`` and ``second``: boolean flags describing
  the components identified by the parser. They are not the numeric date/time values.

Register the entity and name the parameter so that a state body can retrieve it from the
matched intent:

.. code:: python

    from datetime import datetime

    from baf.core.agent import Agent
    from baf.core.session import Session
    from baf.library.entity.base_entities import datetime_entity

    agent = Agent('appointment_agent')
    agent.add_entity(datetime_entity)
    appointment_intent = agent.new_intent('appointment_intent', [
        'Schedule an appointment for DATE',
    ])
    appointment_intent.parameter('date', 'DATE', datetime_entity)

    def appointment_body(session: Session):
        prediction = session.event.predicted_intent
        date_param = prediction.get_parameter('date')
        if date_param is None or date_param.value is None:
            session.reply('Please provide a date or time for the appointment.')
            return

        requested_datetime = datetime.fromisoformat(date_param.value)
        original_text = date_param.info['frag']
        session.reply(f'You said: {original_text}')
        session.reply(f'Parsed date-time: {requested_datetime.isoformat()}')

        if date_param.info['year'] and date_param.info['month'] and date_param.info['day']:
            session.set('appointment_date', requested_datetime.date().isoformat())
        if date_param.info['hour']:
            session.set('appointment_time', requested_datetime.timetz().isoformat())
        else:
            session.reply('What time should the appointment be?')

Use this body in the state reached after matching ``appointment_intent`` (see
:any:`intents-with-parameters`). ``date()`` extracts a Python date, while ``timetz()``
extracts a time retaining the parsed UTC offset. Neither method tells you whether the user
supplied that component; inspect ``info`` before relying on it. For example, ``tomorrow``
sets the date flags but leaves the time flags false, although ``value`` still contains a time.

Relative expressions are resolved using the current date/time and the agent's
:any:`NLP_TIMEZONE <baf.nlp.NLP_TIMEZONE>` setting. Configure the intended timezone rather than interpreting
a normalized value as UTC automatically. The flags are parser heuristics; in particular,
the current parser treats a zero time (midnight) as unspecified, so do not use ``hour=False``
to reject an otherwise valid midnight appointment. Ask the user to clarify when needed.

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.add_entity(): :meth:`baf.core.agent.Agent.add_entity`
- Agent.new_entity(): :meth:`baf.core.agent.Agent.new_entity`
- Entity: :class:`baf.core.entity.entity.Entity`
- EntityEntry: :class:`baf.core.entity.entity_entry.EntityEntry`
- Intent: :class:`baf.core.intent.intent.Intent`
- Intent.parameter(): :meth:`baf.core.intent.intent.Intent.parameter`
- IntentClassifierPrediction: :class:`baf.nlp.intent_classifier.intent_classifier_prediction.IntentClassifierPrediction`
- MatchedParameter: :class:`baf.nlp.ner.matched_parameter.MatchedParameter`
- ReceiveTextEvent: :class:`baf.library.transition.events.base_events.ReceiveTextEvent`
- Session: :class:`baf.core.session.Session`
- Session.reply(): :meth:`baf.core.session.Session.reply`
- Session.set(): :meth:`baf.core.session.Session.set`

