"""Definition of the agent properties within the ``agent`` section:"""

from besser.agent.core.property import Property

SECTION_AGENT = 'agent'

CHECK_TRANSITIONS_DELAY = Property(SECTION_AGENT, 'agent.check_transitions.delay', float, 1.0)
"""
An agent evaluates periodically all the transitions from the current state to check if someone is satisfied.

This property sets the delay between each transitions evaluation, in seconds.

name: ``agent.check_transitions.delay``

type: ``float``

default value: ``1``
"""