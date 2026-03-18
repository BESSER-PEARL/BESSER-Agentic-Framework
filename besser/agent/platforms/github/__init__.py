"""Definition of the agent properties within the ``github_platform`` section:"""

from besser.agent.core.property import Property

GITHUB_PERSONAL_TOKEN = Property('platforms.github.personal_token', str, None)
"""
The Personal Access Token used to connect to the GitHub API

name: ``github.personal_token``

type: ``str``

default value: ``None``
"""

GITHUB_WEBHOOK_TOKEN = Property('platforms.github.webhook_token', str, None)
"""
The secret token defined at the webhook creation

name: ``github.webhook_token``

type: ``str``

default value: ``None``
"""

GITHUB_WEBHOOK_PORT = Property('platforms.github.webhook_port', int, 8901)
"""
The server local port. This port should be exposed of proxied to make it visible by GitHub

name: ``github.webhook_port``

type: ``int``

default value: ``8901``
"""
