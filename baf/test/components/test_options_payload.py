"""The message of an AGENT_REPLY_OPTIONS payload: buttons, plus an optional label."""
import json

from baf.platforms.payload import decode_options_message, encode_options_message


def test_options_without_a_label_keep_the_original_shape():
    message = encode_options_message(['Yes', 'No'])

    assert json.loads(message) == {'0': 'Yes', '1': 'No'}
    assert decode_options_message(message) == (['Yes', 'No'], None)


def test_label_travels_with_the_options():
    message = encode_options_message(['Oui', 'Non'], label='Choisissez une option')

    assert decode_options_message(message) == (['Oui', 'Non'], 'Choisissez une option')


def test_empty_label_is_not_sent():
    assert 'label' not in json.loads(encode_options_message(['A'], label=''))
