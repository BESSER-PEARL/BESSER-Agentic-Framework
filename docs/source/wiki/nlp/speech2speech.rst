Speech-to-Speech
================

BAF allows you to simulate a spoken conversation with an agent! To do this, it
implements a Speech-to-Text component (also known as automatic speech recognition, STT or S2T) and combines it with a
Text-to-Speech component (also known as speech synthesis, TTS or T2S). It solves the NLP task
of transcribing an audio file, treating the transcription as a typical user text message and sending it to an LLM, then
converting the text answer by the LLM into audio speech signals.

How to implement
----------------

Let's see how to seamlessly integrate a Speech2Speech component into our agent. You can also check the :doc:`../../examples/speech2speech_agent` for a complete example.

We are going to implement the HFText2Speech class (make sure the the corresponding agent property is set
accordingly). We start by creating our Agent:

.. code:: python

    agent = Agent('example_agent')

The Agent implements the corresponding Speech2Text and Text2Speech classes in the background (eg. HFSpeech2Text, HFText2Speech) based on the set
agent properties. The STT and TTS components are accessible through the Session parameter. When called, they return the transcribed text and the synthesised
audio respectively which can then be send back to the user. It is possible to simulate a spoken conversation by passing
the spoken user message to an LLM after it has been transcribed by the Speech2Text model. The following shows an example
where the transcribed message is passed to an LLM and the answer provided by the LLM is returned back as a spoken message.

First, let's define the LLM:

.. code:: python

    gpt = LLMOpenAI(
        agent=agent,
        name='gpt-4o-mini',
        parameters={},
        num_previous_messages=100,
    )

Within any agent state, the transcribed message can be passed to the LLM by accessing the Session parameter (use the
chat() function to store the chat history. The response by the LLM can the be passed to the TTS component and send back
to the user as an audio message:

.. code:: python

    def stt_body(session: Session):
        tts = session._agent._nlp_engine._text2speech
        # only transcribe message if the user spoke
        if isinstance(session.event, ReceiveJSONEvent) or isinstance(session.event, ReceiveMessageEvent):
            session.reply("User: " + session.event.message)
        answer = gpt.chat(session)
        audio = tts.text2speech(answer)
        websocket_platform.reply_speech(session, audio)
        session.reply(answer)

We can even go a step further and include File input through the Streamlit UI.

Adding Files to a Speech2Speech Agent
-------------------------------------

It is possible to have the user upload files through the Streamlit UI, containing either a spoken or a written message.
We can check for the mime type to differentiate between a Speech2Text or a Text2Speech task:

.. code:: python

    # Execute when a file is received
    def stt_file_body(session: Session):
    stt = session._agent._nlp_engine._speech2text
    tts = session._agent._nlp_engine._text2speech
    event: ReceiveFileEvent = session.event
    file: File = event.file

    # Determine MIME type
    ext = file.name.lower()
    # do only for text files
    if ext.endswith(".txt"):
        mime_type = "text/plain"
    elif ext.endswith(".wav"):
        mime_type = "audio/wav"
    elif ext.endswith(".mp3"):
        mime_type = "audio/mpeg"
    elif ext.endswith(".m4a"):
        mime_type = "audio/mp4"
    else:
        mime_type = "application/octet-stream"

    # only when audio files are uploaded
    if not mime_type == "text/plain":

        # set mime type property
        agent.set_property(nlp.NLP_STT_MIME_TYPE, mime_type)

        # convert file to byte representation
        base64_content = file._base64
        # Decode the base64 string into bytes
        file_bytes = base64.b64decode(base64_content)
        # add to logger
        logger.info(f"Successfully decoded {len(file_bytes)} bytes.")

        # call LuxASR Speech2Text and get transcription
        text= stt.speech2text(file_bytes)
        session.reply("User: " + text)
        answer = gpt.chat(session)
        # answer = gpt.predict(text)
        file_text = answer
    else:
        # convert file to byte representation
        base64_content = file._base64
        # Decode the base64 string into text
        decoded = base64.b64decode(base64_content).decode('utf-8')
        session.reply("User: " + decoded)
        answer = gpt.chat(session)
        file_text = answer

    # call HF Speech2Text and get transcription
    audio = tts.text2speech(file_text)

    session.reply(file_text)
    websocket_platform.reply_speech(session, audio)

API References
--------------

- Agent: :class:`besser.agent.core.agent.Agent`
- APISpeech2Text: :class:`besser.agent.nlp.speech2text.api_speech2text.APISpeech2Text`
- HFSpeech2Text: :class:`besser.agent.nlp.speech2text.hf_speech2text.HFSpeech2Text`
- HFText2Speech: :class:`besser.agent.nlp.text2speech.hf_text2speech.HFText2Speech`
- LuxASRSpeech2Text: :class:`besser.agent.nlp.speech2text.luxasr_speech2text.LuxASRSpeech2Text`
- NLPEngine: :class:`besser.agent.core.nlp.nlp_engine.NLPEngine`
- OpenAISpeech2Text: :class:`besser.agent.nlp.speech2text.openai_speech2text.OpenAISpeech2Text`
- OpenAIText2Speech: :class:`besser.agent.nlp.text2speech.openai_text2speech.OpenAIText2Speech`
- PiperText2Speech: :class:`besser.agent.nlp.text2speech.piper_text2speech.PiperText2Speech`
- Session: :class:`besser.agent.core.session.Session`
- Session.reply(): :meth:`besser.agent.core.session.Session.reply`
- Speech2Text: :class:`besser.agent.nlp.speech2text.speech2text.Speech2Text`
- Text2Speech: :class:`besser.agent.nlp.text2speech.text2speech.Text2Speech`