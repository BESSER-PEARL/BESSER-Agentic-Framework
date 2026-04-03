"""Definition of the agent properties within the ``telegram_platform`` section:"""

from baf.core.property import Property

TELEGRAM_TOKEN = Property('platforms.telegram.token', str, None)
"""
The Telegram Bot token. Used to connect to the Telegram Bot

type: ``str``

default value: ``None``
"""
