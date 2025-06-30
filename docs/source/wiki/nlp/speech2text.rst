Speech-to-Text
==============

BAF allows you to use your voice to interact with the agents, transforming them into voicebots! To do this, it
implements a Speech-to-Text component (also known as automatic speech recognition, STT or S2T). It solves the NLP task
of transcribing an audio file. Then, the transcription is treated as a typical user text message.

Available Speech-to-Text models
-------------------------------

BAF supports a variety of implementations for speech-to-text:

- :class:`~besser.agent.nlp.speech2text.hf_speech2text.HFSpeech2Text`: For `HuggingFace <https://huggingface.co/>`_ STT
  models, you need to set the :obj:`~besser.agent.nlp.NLP_STT_HF_MODEL` agent property. Example model: ``openai/whisper-tiny`` (very lightweight model)

- :class:`~besser.agent.nlp.speech2text.api_speech2text.APISpeech2Text`: For the
  `SpeechRecognition <https://github.com/Uberi/speech_recognition>`_ Python library. You need to set the
  :obj:`~besser.agent.nlp.NLP_STT_SR_ENGINE` agent property (Currently only supports Google Speech Recognition).

- :class:`~besser.agent.nlp.speech2text.openai_speech2text.OpenAISpeech2Text`: For
  `OpenAI <https://platform.openai.com/docs/guides/speech-to-text>`_ STT models. You need to set the
  :obj:`~besser.agent.nlp.NLP_STT_OPENAI_MODEL` agent property. Example model: ``whisper-1``

- :class:`~besser.agent.nlp.speech2text.luxasr_speech2text.LuxASRSpeech2Text`: For the `LuxASR <https://luxasr.uni.lu/>`_
  API. You need to set the :obj:`~besser.agent.nlp.NLP_STT_MIME_TYPE` agent property. Example: ``application/octet-stream``.
  Optional agent properties:

- :obj:`~besser.agent.nlp.NLP_STT_DIARIZATION`. Example ``Enabled`` (default)

- :obj:`~besser.agent.nlp.NLP_STT_OUT_FMT`. Example ``text`` (default)

How to use
----------

Let's see how to seamlessly integrate a Speech2Text model into our agent. You can also check the :doc:`../../examples/speech2text_agent` for a complete example.

We are going to implement the HFSpeech2Text class (make sure the the corresponding agent property is set
accordingly). We start by creating our Agent:

.. code:: python

    agent = Agent('example_agent')


The Agent builds the NLP Engine, which implements the corresponding Speech2Text class in the background (eg. HFSpeech2Text) based on the set
agent property. The Speech2Text component will be automatically called when the user speaks into the microphone through
the Streamlit UI and the transcribed message can be used within any agent state and simply accessed through the Session
parameter.

.. code:: python

    def stt_body(session: Session):
        session.reply("User: " + session.event.message)

There are plenty of possibilities to take advantage of Speech2Text models in an agent. The previous is a very simple use
case, but we can do more advanced tasks by combining the Speech2Text module with an :class:`~besser.agent.nlp.llm.llm.LLM`.

Combining Speech2Text with LLM responses
----------------------------------------

It is possible to simulate a conversation by passing the spoken user message to an LLM after it has been transcribed by
the Speech2Text model. The following shows an example where the transcribed message is passed to an LLM:

First, let's define the LLM:

.. code:: python

    gpt = LLMOpenAI(
        agent=agent,
        name='gpt-4o-mini',
        parameters={},
        num_previous_messages=100,
    )

Within any agent state, the transcribed message can be passed to the LLM by accessing the Session parameter:

.. code:: python

    def stt_body(session: Session):
        session.reply("User: " + session.event.message)
        answer = gpt.predict(session.event.message)
        session.reply(answer)

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- APISpeech2Text: :class:`besser.agent.nlp.speech2text.api_speech2text.APISpeech2Text`
- HFSpeech2Text: :class:`besser.agent.nlp.speech2text.hf_speech2text.HFSpeech2Text`
- LuxASRSpeech2Text: :class:`besser.agent.nlp.speech2text.luxasr_speech2text.LuxASRSpeech2Text`
- NLPEngine: :class:`besser.agent.core.nlp.nlp_engine.NLPEngine`
- OpenAISpeech2Text: :class:`besser.agent.nlp.speech2text.openai_speech2text.OpenAISpeech2Text`
- Session: :class:`besser.agent.core.session.Session`
- Session.reply(): :meth:`besser.agent.core.session.Session.reply`
- Speech2Text: :class:`besser.agent.nlp.speech2text.speech2text.Speech2Text`