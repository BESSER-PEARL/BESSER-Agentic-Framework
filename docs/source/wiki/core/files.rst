Files
=====

The :class:`File <baf.core.file.File>` class was added as a way to help with the definition of file objects that are both sent and received by users.

File Object Definition
----------------------
A file object consists of 3 attributes: 

- name (str): The name of the file.
- type (str): The type of the file.
- base64 (str): The base64 representation of the file.

Yet, to create a file object using the constructor, 3 options are possible. 

- Providing the file content as a base64 string
- Providing a file path
- Providing the raw file data, in bytes



With this, we want to allow users to choose the option that is easiest to them and take care of the necessary conversion. 
Thus, users can choose whether to set file_base64, file_path or file_data.

Receiving and Sending Files
---------------------------

Define a :meth:`~baf.core.state.State.when_file_received` transition on the state that waits for a file.
The ``allowed_types`` argument takes MIME type strings, for example ``"audio/wav"`` for a WAV audio file,
or a list such as ``["application/pdf", "image/png"]`` to accept several types.

.. code:: python

    from baf.core.agent import Agent
    from baf.core.session import Session

    agent = Agent('file_receiver')
    waiting_state = agent.new_state('waiting', initial=True)
    received_state = agent.new_state('received')

    def received_body(session: Session):
        file = session.event.file
        session.reply(f'Received {file.name} ({file.type})')

    received_state.set_body(received_body)
    waiting_state.when_file_received(
        allowed_types=['application/pdf', 'image/png']
    ).go_to(received_state)
    received_state.go_to(waiting_state)

To accept a single type, replace the list with a string, for example ``allowed_types='audio/wav'``.
To accept any file type, omit ``allowed_types`` or set it to ``None``. The MIME type is compared with
the received :class:`File <baf.core.file.File>` object's ``type`` attribute. See also
:ref:`the built-in file reception transition <file-reception-transition>`.

In case a file transition was specified, once it takes place the file object will be available in the
Session's event:

.. code:: python

    def body(session: Session):
        event: ReceiveFileEvent = session.event
        file: File = event.file
        file_name = file.name
        file_type = file.type
        file_base64_data = file.base64
        # further processing here

For sending files to the users, agent creators will first have to create a file object and use the following
platform-specific function (not every platform might support it): 

.. code:: python

    def body(session: Session):
        file = File(file_name="name", file_type="type", file_base64="file_base64")
        websocket_platform.reply_file(session=session, file=file)
        # OR
        telegram_platform.reply_file(session=session, file=file)
        # in case you want to add a caption to your file, you can also set the message parameter
        telegram_platform.reply_file(session=session, file=file, message="Your Message")    

API References
--------------

- File: :class:`baf.core.file.File`
- State.when_file_received(): :meth:`baf.core.state.State.when_file_received`
- ReceiveFileEvent: :class:`baf.library.transition.events.base_events.ReceiveFileEvent`
- Session: :class:`baf.core.session.Session`
- TelegramPlatform.reply_file(): :meth:`baf.platforms.telegram.telegram_platform.TelegramPlatform.reply_file`
- WebSocketPlatform.reply_file(): :meth:`baf.platforms.websocket.websocket_platform.WebSocketPlatform.reply_file`
