"""
The collection of preexisting intents.
"""

from baf.core.intent.intent import Intent

fallback_intent = Intent(name='fallback_intent')
"""The Fallback Intent. Used when no intent is matched by the Intent Classifier."""
