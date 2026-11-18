RAG agent
=========

The initial state accepts file uploads and questions. File events lead to ``upload_file_state``;
text that does not match an intent leads to ``ask_question_state`` through
:meth:`~baf.core.state.State.when_no_intent_matched`. The question-answering body reads the text from
``session.event.message``. This fallback transition changes state, unlike a state's fallback body, which runs
without leaving the current state.

.. literalinclude:: ../../../baf/test/examples/rag_agent.py
   :language: python
   :linenos:
