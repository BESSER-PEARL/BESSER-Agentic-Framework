import unittest
from types import SimpleNamespace
from unittest.mock import patch

import boto3
from botocore.stub import Stubber
from botocore.validate import validate_parameters

from baf.core.message import MessageType
from baf.nlp.llm.llm_bedrock_api import LLMBedrock


class BedrockTests(unittest.TestCase):
    def setUp(self):
        agent = SimpleNamespace(nlp_engine=SimpleNamespace(_llms={}))
        self.llm = LLMBedrock(agent, 'test-model', {'inferenceConfig': {'maxTokens': 50}},
                              global_context='global', region_name='us-east-1')
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1',
                                   aws_access_key_id='test', aws_secret_access_key='test')
        with patch('boto3.client', return_value=self.client) as factory:
            self.llm.initialize()
        factory.assert_called_once_with('bedrock-runtime', region_name='us-east-1')
        self.stub = Stubber(self.client)
        self.stub.activate()
        self.addCleanup(self.stub.deactivate)

    def response(self, expected):
        validate_parameters(expected, self.client.meta.service_model.operation_model('Converse').input_shape)
        self.stub.add_response('converse', {
            'output': {'message': {'role': 'assistant', 'content': [{'text': 'answer'}]}},
            'stopReason': 'end_turn', 'usage': {'inputTokens': 1, 'outputTokens': 1, 'totalTokens': 2},
            'metrics': {'latencyMs': 1},
        }, expected)

    def test_predict_context_and_parameters(self):
        session = SimpleNamespace(id='user')
        self.llm.add_user_context(session, 'personal', 'name')
        self.response({'modelId': 'test-model', 'messages': [{'role': 'user', 'content': [{'text': 'hello'}]}],
                       'system': [{'text': 'global'}, {'text': 'personal\n'}, {'text': 'instruction'}],
                       'inferenceConfig': {'maxTokens': 50}})
        self.assertEqual(self.llm.predict('hello', session=session, system_message='instruction'), 'answer')
        self.stub.assert_no_pending_responses()

    def test_chat_and_parameter_override(self):
        session = SimpleNamespace(id='user', get_chat_history=lambda n: [
            SimpleNamespace(type=MessageType.STR, is_user=True, content='hello'),
            SimpleNamespace(type=MessageType.STR, is_user=False, content='hi'),
            SimpleNamespace(type=MessageType.IMAGE, is_user=True, content='image')])
        self.response({'modelId': 'test-model', 'messages': [
            {'role': 'user', 'content': [{'text': 'hello'}]},
            {'role': 'assistant', 'content': [{'text': 'hi'}]}], 'system': [{'text': 'global'}]})
        self.assertEqual(self.llm.chat(session, parameters={}), 'answer')
        self.stub.assert_no_pending_responses()

    def test_invalid_history_count(self):
        self.llm.set_num_previous_messages(0)
        with self.assertRaises(ValueError):
            self.llm.chat(SimpleNamespace(id='user'))

class BedrockAPIKeyTests(unittest.TestCase):
    def test_api_key_is_sent_as_bearer_token(self):
        import json
        from botocore.awsrequest import AWSResponse

        class Body:
            def stream(self, amt=None):
                yield json.dumps({'output': {'message': {'role': 'assistant', 'content': [{'text': 'ok'}]}},
                                  'stopReason': 'end_turn', 'usage': {'inputTokens': 1, 'outputTokens': 1,
                                  'totalTokens': 2}, 'metrics': {'latencyMs': 1}}).encode()

        environment = {'AWS_BEARER_TOKEN_BEDROCK': 'test-api-key', 'AWS_EC2_METADATA_DISABLED': 'true'}
        with patch.dict('os.environ', environment, clear=True):
            session = boto3.Session(region_name='us-east-1')
            agent = SimpleNamespace(nlp_engine=SimpleNamespace(_llms={}))
            llm = LLMBedrock(agent, 'test-model', region_name='us-east-1')
            with patch('boto3.client', side_effect=session.client):
                llm.initialize()
            response = AWSResponse('https://example.invalid', 200, {}, Body())
            with patch.object(llm.client._endpoint.http_session, 'send', return_value=response) as send:
                self.assertEqual(llm.predict('hello'), 'ok')
            request = send.call_args.args[0]
            authorization = request.headers['Authorization']
            if isinstance(authorization, bytes):
                authorization = authorization.decode()
            self.assertEqual(authorization, 'Bearer test-api-key')


if __name__ == '__main__':
    unittest.main()
