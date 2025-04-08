Files
=====

The :class:`File <besser.agent.core.file.File>` class was added as a way to help with the definition of file objects that are both sent and received by users.

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

- File: :class:`besser.agent.core.file.File`
- ReceiveFileEvent: :class:`besser.agent.library.transition.events.base_events.ReceiveFileEvent`
- Session: :class:`besser.agent.core.session.Session`
- TelegramPlatform.reply_file(): :meth:`besser.agent.platforms.telegram.telegram_platform.TelegramPlatform.reply_file`
- WebSocketPlatform.reply_file(): :meth:`besser.agent.platforms.websocket.websocket_platform.WebSocketPlatform.reply_file`
