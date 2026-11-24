"""Client for `Jev <https://docs.typesafe.ai>`_, TypeSafe AI's typed decision model.

Jev answers typed questions about a piece of text (the *state*) with calibrated probabilities instead of free text:

- :class:`Noul`: a yes/no question. The answer is the probability that the condition holds.
- :class:`Choice`: pick one option out of a set. The answer is the winning option plus a probability per option.
- :class:`Score`: place the state on an ordered scale. The answer is the expected level plus a probability per level.

Several questions can be asked over the same state in one request; they are evaluated independently.
"""

from __future__ import annotations

import random
import time
from typing import Any, TYPE_CHECKING, Union

import requests

from baf import nlp
from baf.exceptions.logger import logger

if TYPE_CHECKING:
    from baf.core.agent import Agent

JEV_DEFAULT_BASE_URL = 'https://api.typesafe.ai'
JEV_DEFAULT_MODEL = 'jev-latest'
JEV_SYSTEM_ONE_PATH = '/v1/systemone'
_RETRY_STATUSES = {408, 429, 500, 502, 503, 504, 529}


class JevError(Exception):
    """Raised when a request to the Jev API fails.

    Args:
        message (str): the error message
        status (int or None): the HTTP status code, if the API answered
        body (Any): the response body, if any

    Attributes:
        status (int or None): the HTTP status code, if the API answered
        body (Any): the response body, if any
    """

    def __init__(self, message: str, status: int = None, body: Any = None):
        super().__init__(message)
        self.status: int or None = status
        self.body: Any = body


class JevQuestion:
    """A typed question for Jev. Use one of its subclasses: :class:`Noul`, :class:`Choice` or :class:`Score`.

    Args:
        type (str): the question type ('noul', 'choice' or 'score')
        instructions (str): what Jev has to decide about the state
        criteria (Any): the type-specific criteria

    Attributes:
        type (str): the question type ('noul', 'choice' or 'score')
        instructions (str): what Jev has to decide about the state
        criteria (Any): the type-specific criteria
    """

    def __init__(self, type: str, instructions: str, criteria: Any = None):
        self.type: str = type
        self.instructions: str = instructions
        self.criteria: Any = criteria

    def to_json(self) -> dict:
        """Get the JSON body of the question, as the Jev API expects it.

        Returns:
            dict: the question body
        """
        body = {'type': self.type, 'instructions': self.instructions}
        if self.criteria is not None:
            body['criteria'] = self.criteria
        return body


class Noul(JevQuestion):
    """A yes/no question. Jev answers with the probability that the condition is true.

    Args:
        instructions (str): the condition to evaluate (e.g., 'Does the message ask for a refund?')
        true (str or None): optional description of what counts as true
        false (str or None): optional description of what counts as false
    """

    def __init__(self, instructions: str, true: str = None, false: str = None):
        criteria = None
        if true is not None or false is not None:
            criteria = {'true': true, 'false': false}
        super().__init__('noul', instructions, criteria)


class Choice(JevQuestion):
    """Pick one option out of a set. Jev answers with the winning option and a probability per option.

    Args:
        instructions (str): what to choose (e.g., 'Which department should handle this ticket?')
        options (dict[str, str or None] or list[str]): the options. As a dict, keys are option names and values their
            descriptions (None for self-explanatory names). As a list, option names without descriptions. At least 2
            options.
    """

    def __init__(self, instructions: str, options: Union[dict[str, str or None], list[str]]):
        if isinstance(options, (list, tuple)):
            options = {option: None for option in options}
        if len(options) < 2:
            raise ValueError('A Jev Choice question needs at least 2 options')
        super().__init__('choice', instructions, dict(options))


class Score(JevQuestion):
    """Place the state on an ordered scale. Jev answers with the expected level and a probability per level.

    Args:
        instructions (str): what to score (e.g., 'How urgent is this ticket?')
        levels (list[str]): the level descriptions, from lowest (level 0) to highest. At least 2 levels.
    """

    def __init__(self, instructions: str, levels: list[str]):
        if len(levels) < 2:
            raise ValueError('A Jev Score question needs at least 2 levels')
        super().__init__('score', instructions, list(levels))


class JevAnswer:
    """Jev's answer to one question.

    Args:
        question_id (str): the id the question was asked with
        json (dict): the raw answer returned by the API

    Attributes:
        question_id (str): the id the question was asked with
        type (str): the question type ('noul', 'choice' or 'score')
        noul (float or None): for Noul questions, the probability that the condition is true
        choice (str or None): for Choice questions, the most probable option
        score (float or None): for Score questions, the expected level (sum of level x probability; may be fractional)
        probabilities (dict or None): for Choice questions, option -> probability; for Score questions,
            level (int) -> probability
        legend (dict or None): for Score questions, level (int) -> level description
        confidence (float or None): for Choice and Score questions, how concentrated the probabilities are (0 to 1).
            None if the API did not return it
        json (dict): the raw answer returned by the API
    """

    def __init__(self, question_id: str, json: dict):
        self.question_id: str = question_id
        self.json: dict = json
        self.type: str = json.get('type')
        self.noul: float or None = json.get('noul')
        self.choice: str or None = json.get('choice')
        self.score: float or None = json.get('score')
        self.confidence: float or None = json.get('confidence')
        probabilities = json.get('probabilities')
        legend = json.get('legend')
        if self.type == 'score':
            # Over HTTP, score levels are string keys ("0", "1", ...). Expose them as ints.
            probabilities = {int(k): v for k, v in probabilities.items()} if probabilities else probabilities
            legend = {int(k): v for k, v in legend.items()} if legend else legend
        self.probabilities: dict or None = probabilities
        self.legend: dict or None = legend

    @property
    def value(self) -> Any:
        """Any: the main value of the answer: ``noul`` for Noul, ``choice`` for Choice and ``score`` for Score."""
        return {'noul': self.noul, 'choice': self.choice, 'score': self.score}.get(self.type)

    def __repr__(self):
        return f'JevAnswer({self.question_id}={self.value!r}, type={self.type}, confidence={self.confidence})'


class JevResponse:
    """The response of Jev to a set of questions.

    Args:
        json (dict): the raw response returned by the API

    Attributes:
        model (str or None): the exact model version that answered (e.g., 'jev-1.13.0')
        answers (dict[str, JevAnswer]): the answers, keyed by question id
        usage (dict or None): token usage (input_tokens, output_tokens)
        json (dict): the raw response returned by the API
    """

    def __init__(self, json: dict):
        self.json: dict = json
        self.model: str or None = json.get('model')
        self.answers: dict[str, JevAnswer] = {
            question_id: JevAnswer(question_id, answer) for question_id, answer in json.get('answers', {}).items()
        }
        self.usage: dict or None = json.get('usage')

    def __getitem__(self, question_id: str) -> JevAnswer:
        return self.answers[question_id]


class Jev:
    """A client for Jev, TypeSafe AI's typed decision model.

    Creating it with an agent registers it in the agent's NLP engine, so a state using a
    :class:`~baf.nlp.intent_classifier.intent_classifier_configuration.JevIntentClassifierConfiguration` uses it.

    The API key is read from the :obj:`~baf.nlp.TYPESAFE_API_KEY` agent property (``nlp.typesafe.api_key``) when the
    agent starts, unless one is given here.

    Jev also runs behind other gateways (OpenRouter, Vercel AI Gateway, a LiteLLM proxy...). For those, set ``base_url``
    and ``path`` to the gateway's endpoint and ``model`` to the gateway's model id.

    Args:
        agent (Agent or None): the agent the client belongs to. Can be None to use Jev outside an agent (then pass
            ``api_key``)
        model (str): the model to use. Defaults to 'jev-latest'. Pin a version (e.g., 'jev-1.13.0') if you tune
            thresholds on its probabilities
        api_key (str or None): the TypeSafe API key. If None, the agent property is used
        base_url (str): the API base URL
        path (str): the endpoint path
        timeout (float): seconds to wait for each HTTP request
        max_retries (int): how many times to retry on rate limits (429), overload (529), timeouts and server errors

    Attributes:
        model (str): the model to use
        base_url (str): the API base URL
        path (str): the endpoint path
        timeout (float): seconds to wait for each HTTP request
        max_retries (int): how many times to retry on rate limits, overload, timeouts and server errors
    """

    def __init__(
            self,
            agent: 'Agent' = None,
            model: str = JEV_DEFAULT_MODEL,
            api_key: str = None,
            base_url: str = JEV_DEFAULT_BASE_URL,
            path: str = JEV_SYSTEM_ONE_PATH,
            timeout: float = 10.0,
            max_retries: int = 2
    ):
        self._agent: 'Agent' = agent
        self._api_key: str or None = api_key
        self.model: str = model
        self.base_url: str = base_url.rstrip('/')
        self.path: str = path
        self.timeout: float = timeout
        self.max_retries: int = max_retries
        self._http: requests.Session = requests.Session()
        if agent is not None:
            agent.nlp_engine._jev = self

    def initialize(self) -> None:
        """Read the API key from the agent properties, if none was given. Called when the agent starts."""
        if self._api_key is None and self._agent is not None:
            self._api_key = self._agent.get_property(nlp.TYPESAFE_API_KEY)
        if not self._api_key:
            logger.warning(f"Jev has no API key. Set the '{nlp.TYPESAFE_API_KEY.name}' agent property or pass api_key.")

    def ask(
            self,
            state: Union[str, dict, list],
            questions: dict[str, Union[JevQuestion, dict]],
            model: str = None
    ) -> JevResponse:
        """Ask Jev one or more typed questions about a state.

        Args:
            state (str or dict or list): the content to decide about (e.g., the user message, or a dict with the
                message and some context)
            questions (dict[str, JevQuestion or dict]): the questions, keyed by an id of your choice. The answers come
                back under the same ids. Raw dicts in the API format are also accepted
            model (str or None): the model to use for this request. If None, the client's model is used

        Returns:
            JevResponse: the answers

        Raises:
            JevError: if the request fails (after the retries) or the response cannot be read
        """
        if not questions:
            raise ValueError('Jev needs at least 1 question')
        if self._api_key is None:
            self.initialize()
        body = {
            'state': state,
            'model': model or self.model,
            'questions': {
                question_id: question.to_json() if isinstance(question, JevQuestion) else question
                for question_id, question in questions.items()
            },
        }
        return JevResponse(self._post(body))

    def noul(self, state: Union[str, dict, list], instructions: str, true: str = None, false: str = None) -> float:
        """Ask a single yes/no question.

        Args:
            state (str or dict or list): the content to decide about
            instructions (str): the condition to evaluate
            true (str or None): optional description of what counts as true
            false (str or None): optional description of what counts as false

        Returns:
            float: the probability that the condition is true
        """
        return self.ask(state, {'q': Noul(instructions, true, false)})['q'].noul

    def choice(self, state: Union[str, dict, list], instructions: str,
               options: Union[dict[str, str or None], list[str]]) -> JevAnswer:
        """Ask a single Choice question.

        Args:
            state (str or dict or list): the content to decide about
            instructions (str): what to choose
            options (dict[str, str or None] or list[str]): the options (see :class:`Choice`)

        Returns:
            JevAnswer: the answer (``choice``, ``probabilities``, ``confidence``)
        """
        return self.ask(state, {'q': Choice(instructions, options)})['q']

    def score(self, state: Union[str, dict, list], instructions: str, levels: list[str]) -> JevAnswer:
        """Ask a single Score question.

        Args:
            state (str or dict or list): the content to decide about
            instructions (str): what to score
            levels (list[str]): the level descriptions, from lowest to highest

        Returns:
            JevAnswer: the answer (``score``, ``probabilities``, ``legend``, ``confidence``)
        """
        return self.ask(state, {'q': Score(instructions, levels)})['q']

    def _post(self, body: dict) -> dict:
        url = self.base_url + self.path
        headers = {'Authorization': f'Bearer {self._api_key}', 'Content-Type': 'application/json'}
        attempt = 0
        while True:
            try:
                response = self._http.post(url, json=body, headers=headers, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt, None)
                    attempt += 1
                    continue
                raise JevError(f'Could not reach Jev at {url}: {e}') from e
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    raise JevError('Jev returned a response that is not JSON', response.status_code,
                                   response.text) from e
            if response.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                self._sleep_before_retry(attempt, response.headers.get('retry-after'))
                attempt += 1
                continue
            try:
                error_body = response.json()
            except ValueError:
                error_body = response.text
            raise JevError(f'Jev request failed with status {response.status_code}: {error_body}',
                           response.status_code, error_body)

    @staticmethod
    def _sleep_before_retry(attempt: int, retry_after: str or None) -> None:
        delay = min(0.5 * (2 ** attempt), 5.0) * (1 + random.uniform(-0.25, 0.25))
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass
        time.sleep(delay)
