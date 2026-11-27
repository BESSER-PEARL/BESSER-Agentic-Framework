from __future__ import annotations

from typing import TYPE_CHECKING

from baf.core.message import MessageType
from baf.nlp.llm.llm import LLM

if TYPE_CHECKING:
    from baf.core.agent import Agent
    from baf.core.session import Session


class LLMBedrock(LLM):
    """Amazon Bedrock wrapper using the Converse API.

    ``name`` is a Bedrock model or inference profile ID. ``parameters`` are
    passed as Converse request fields, such as ``inferenceConfig`` and
    ``additionalModelRequestFields``. Credentials and region are resolved by
    boto3's standard configuration chain unless ``region_name`` is supplied.
    A Bedrock API key can be supplied through ``AWS_BEARER_TOKEN_BEDROCK``.
    The chosen model must support Converse and any requested system prompts.
    """

    def __init__(self, agent: 'Agent', name: str, parameters: dict = None,
                 num_previous_messages: int = 1, global_context: str = None,
                 region_name: str = None):
        super().__init__(agent, name, parameters or {}, global_context)
        self.num_previous_messages = num_previous_messages
        self.region_name = region_name
        self.client = None

    def initialize(self) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise ImportError('Install boto3 with the llms extra to use LLMBedrock') from exc
        self.client = boto3.client('bedrock-runtime', region_name=self.region_name)

    def set_model(self, name: str) -> None:
        self.name = name

    def set_num_previous_messages(self, num_previous_messages: int) -> None:
        self.num_previous_messages = num_previous_messages

    def _converse(self, messages, parameters, session, system_message):
        context = [self._global_context]
        if session is not None:
            context.append(self._user_context.get(session.id))
        context.append(system_message)
        request = dict(self.parameters if parameters is None else parameters)
        request.update(modelId=self.name, messages=messages)
        system = [{'text': item} for item in context if item]
        if system:
            request['system'] = system
        response = self.client.converse(**request)
        return ''.join(block['text'] for block in response['output']['message']['content'] if 'text' in block)

    def predict(self, message: str, parameters: dict = None, session: 'Session' = None,
                system_message: str = None) -> str:
        return self._converse([{'role': 'user', 'content': [{'text': message}]}],
                              parameters, session, system_message)

    def chat(self, session: 'Session', parameters: dict = None, system_message: str = None) -> str:
        if self.num_previous_messages <= 0:
            raise ValueError('The number of previous messages to send to the LLM must be > 0')
        messages = [{'role': 'user' if item.is_user else 'assistant',
                     'content': [{'text': str(item.content)}]}
                    for item in session.get_chat_history(n=self.num_previous_messages)
                    if item.type in (MessageType.STR, MessageType.LOCATION, MessageType.JSON)]
        return self._converse(messages, parameters, session, system_message)
