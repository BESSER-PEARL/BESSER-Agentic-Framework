Text-to-Speech
==============

BAF allows you to create synthetic speech from your texts! To do this, it
implements a Text-to-Speech component (also known as speech synthesis, TTS or T2S). It solves the NLP task
of converting written text into audio speech signals.

Available Text-to-Speech models
-------------------------------

BAF supports a variety of implementations for text-to-speech:

- :class:`~besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech`: For `HuggingFace <https://huggingface.co/>`_ TTS
  models, you need to set the :obj:`~besser.agent.nlp.NLP_TTS_HF_MODEL` agent property. Example model: ``facebook/mms-tts-eng``
  Optional agent properties:
  - :obj:`~besser.agent.nlp.NLP_TTS_HF_RT`. Example ``pt`` (default None)

- :class:`~besser.agent.nlp.text2speech.openai_text2speech.OpenAIText2Speech`: For
  `OpenAI <https://platform.openai.com/docs/guides/text-to-speech>`_ TTS models. You need to set the
  :obj:`~besser.agent.nlp.NLP_TTS_OPENAI_MODEL` and the :obj:`~besser.agent.nlp.NLP_TTS_OPENAI_VOICE` agent properties.
  Example values: ``gpt-4o-mini-tts`` and ``alloy`` respectively.

- :class:`~besser.agent.nlp.text2speech.piper_text2speech.PiperText2Speech`: For the `Piper <https://github.com/rhasspy/piper>`_
  TTS implementation (Only tested with the following HuggingFace Model mbarnig/lb_rhasspy_piper_tts). You need to download the model and run it through a Docker container
  as Piper currently only works on Linux and set the :obj:`~besser.agent.nlp.NLP_TTS_PIPER_MODEL` agent property. Example: ``mbarnig/lb_rhasspy_piper_tts``.

How to use
----------

Let's see how to seamlessly integrate a Text2Speech model into our agent. You can also check the :doc:`../../examples/text2speech_agent` for a complete example.

We are going to implement the HFText2Speech class (make sure the the corresponding agent property is set
accordingly). We start by creating our Agent:

.. code:: python

    agent = Agent('example_agent')

The Agent builds the NLP Engine, which implements the corresponding Text2Speech class in the background (eg. HFText2Speech) based on the set
agent property. The TTS component is accessible through the Session parameter. When called, it returns the synthesised
audio which can then be send back to the user as an audio message:

.. code:: python

    def tts_body(session: Session):
        tts = session._agent._nlpengine._text2speech
        audio = tts.text2speech(session.event.message)
        websocket_platform.reply_speech(session, audio)


API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- HFText2Speech: :class:`besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech`
- NLPEngine: :class:`besser.agent.core.nlp.nlp_engine.NLPEngine`
- OpenAIText2Speech: :class:`besser.agent.nlp.text2speech.openai_text2speech.OpenAIText2Speech`
- PiperText2Speech: :class:`besser.agent.nlp.text2speech.piper_text2speech.PiperText2Speech`
- Session: :class:`besser.agent.core.session.Session`
- Session.reply(): :meth:`besser.agent.core.session.Session.reply`
- Text2Speech: :class:`besser.agent.nlp.text2speech.text2speech.Text2Speech`