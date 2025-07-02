Text-to-Speech
==============

BAF allows you to create synthetic speech from your texts! To do this, it
implements a Text-to-Speech component (also known as speech synthesis, TTS or T2S). It solves the NLP task
of converting written text into audio speech signals.

Available Text-to-Speech models
-------------------------------

BAF supports a variety of implementations for text-to-speech:

- :class:`~besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech`: For `HuggingFace <https://huggingface.co/>`_ TTS
  models. Example model: ``facebook/mms-tts-eng``
  Optional parameters for :meth:`~besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech.text2speech`:
  - ``return_tensor``. Example ``pt`` (default)

- :class:`~besser.agent.nlp.text2speech.openai_text2speech.OpenAIText2Speech`: For
  `OpenAI <https://platform.openai.com/docs/guides/text-to-speech>`_ TTS models. You can set the optional class parameter
  ``voice`` (default ``alloy``). Example model ``gpt-4o-mini-tts``.

- :class:`~besser.agent.nlp.text2speech.piper_text2speech.PiperText2Speech`: For the `Piper <https://github.com/rhasspy/piper>`_
  TTS implementation (Only tested with the HuggingFace Model mbarnig/lb_rhasspy_piper_tts). You need to download
  the model and run it through a Docker container as Piper currently only works on Linux. Example Model:
  ``mbarnig/lb_rhasspy_piper_tts`` (default).

How to use
----------

Let's see how to seamlessly integrate a Text2Speech model into our agent. You can also check the
:doc:`../../examples/text2speech_agent` for a complete example.

We are going to implement the HFText2Speech class. We start by creating our Agent and defining the TTS model(s):

.. code:: python

    agent = Agent('example_agent')

    tts = HFText2Speech(agent=agent, model_name="facebook/mms-tts-eng")

The Agent builds the NLP Engine, which implements the corresponding Text2Speech class in the background (eg. HFText2Speech).
The TTS component is automatically called through the Websocket Platform reply_speech() function. When called, it returns
the synthesised audio which is then send back to the user as an audio message:

.. code:: python

    def tts_body(session: Session):
        websocket_platform.reply_speech(session, session.event.message)


API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- HFText2Speech: :class:`besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech`
- NLPEngine: :class:`besser.agent.nlp.nlp_engine.NLPEngine`
- OpenAIText2Speech: :class:`besser.agent.nlp.text2speech.openai_text2speech.OpenAIText2Speech`
- PiperText2Speech: :class:`besser.agent.nlp.text2speech.piper_text2speech.PiperText2Speech`
- Session: :class:`besser.agent.core.session.Session`
- Session.reply(): :meth:`besser.agent.core.session.Session.reply`
- Text2Speech: :class:`besser.agent.nlp.text2speech.text2speech.Text2Speech`