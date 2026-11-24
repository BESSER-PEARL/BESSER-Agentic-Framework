from typing import TYPE_CHECKING

from baf.exceptions.logger import logger
from baf.nlp.intent_classifier.intent_classifier import IntentClassifier
from baf.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from baf.nlp.jev.jev import Choice, JevError
from baf.nlp.ner.matched_parameter import MatchedParameter

if TYPE_CHECKING:
    from baf.core.state import State
    from baf.nlp.nlp_engine import NLPEngine

JEV_NONE_OPTION = 'none_of_the_above'
JEV_MAX_CHOICE_OPTIONS = 32
DEFAULT_JEV_INSTRUCTIONS = (
    'Which option is the intent of the user message? Each option describes one intent the user may have.'
)


class JevIntentClassifier(IntentClassifier):
    """An Intent Classifier that uses `Jev <https://docs.typesafe.ai>`_, TypeSafe AI's typed decision model.

    It asks Jev a single Choice question whose options are the state's intents (described by their descriptions and
    some training sentences). Jev returns a calibrated probability for each intent, which becomes the intent score.

    Jev does not extract parameters, so the intent parameters are filled by the agent's NER (if enabled in the
    configuration).

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        state (State): the state the intent classifier belongs to

    See Also:
        :class:`~baf.nlp.intent_classifier.intent_classifier_configuration.JevIntentClassifierConfiguration`.
    """

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: 'State'
    ):
        super().__init__(nlp_engine, state)
        self._question: Choice or None = None

    def _option_description(self, intent) -> str or None:
        config = self._state.ic_config
        parts = []
        if config.use_intent_descriptions and intent.description:
            parts.append(intent.description)
        if config.use_training_sentences and intent.training_sentences and config.max_training_sentences > 0:
            examples = '; '.join(f'"{s}"' for s in intent.training_sentences[:config.max_training_sentences])
            parts.append(f'Examples: {examples}')
        return ' '.join(parts) if parts else None

    def train(self) -> None:
        config = self._state.ic_config
        options: dict[str, str or None] = {
            intent.name: self._option_description(intent) for intent in self._state.intents
        }
        if config.none_option:
            if JEV_NONE_OPTION in options:
                raise ValueError(f"State '{self._state.name}' has an intent named '{JEV_NONE_OPTION}', which the Jev "
                                 f"Intent Classifier uses as its 'none' option. Rename it or set none_option=False.")
            options[JEV_NONE_OPTION] = 'The message does not match any of the other options.'
        if len(options) < 2:
            # Jev needs at least 2 options. With a single intent and no 'none' option, add it anyway.
            options[JEV_NONE_OPTION] = 'The message does not match any of the other options.'
        if len(options) > JEV_MAX_CHOICE_OPTIONS:
            logger.warning(f"The Jev Intent Classifier in state '{self._state.name}' has {len(options)} options. "
                           f"Jev may reject Choice questions with more than {JEV_MAX_CHOICE_OPTIONS} options.")
        self._question = Choice(config.instructions or DEFAULT_JEV_INSTRUCTIONS, options)

    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        jev = self._nlp_engine._jev
        if jev is None:
            logger.error(f"State '{self._state.name}' uses the Jev Intent Classifier but the agent has no Jev client.")
            return []
        if self._question is None:
            self.train()
        try:
            response = jev.ask(message, {'intent': self._question}, model=self._state.ic_config.model)
            answer = response['intent']
        except (JevError, KeyError) as e:
            logger.error(f"An error occurred while predicting the intent in state '{self._state.name}' with the Jev "
                         f"Intent Classifier: {e}")
            return []
        probabilities: dict[str, float] = answer.probabilities or {}
        if not probabilities and answer.choice is not None:
            probabilities = {answer.choice: 1.0}

        intent_matched_parameters = {}
        if self._state.ic_config.use_ner and self._nlp_engine.ner is not None:
            try:
                intent_matched_parameters = self._nlp_engine.ner.predict(self._state, message).intent_matched_parameters
            except Exception as e:
                logger.error(f"NER failed in state '{self._state.name}': {e}")

        predictions: list[IntentClassifierPrediction] = []
        for intent in self._state.intents:
            matched_parameters: list[MatchedParameter] = intent_matched_parameters.get(intent, [])
            predictions.append(IntentClassifierPrediction(
                intent,
                probabilities.get(intent.name, 0.0),
                message,
                matched_parameters
            ))
        return predictions
