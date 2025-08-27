"""Definition of the agent properties within the ``A2A_platfrom`` section:"""

from besser.agent.core.property import Property

SECTION_A2A = 'a2a_platform'

A2A_WEBOSKET_PORT = Property(SECTION_A2A, 'a2a.port', int, 8000)
"""
The server local port. This port should be exposed of proxied to make it visible by other Agents

name: ``a2a.port``

type: ``int``

default value: ``8000``
"""