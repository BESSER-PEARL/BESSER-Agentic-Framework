from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np

from baf import nlp
from baf.core.intent.intent import Intent
from baf.exceptions.logger import logger
from baf.nlp.intent_classifier.intent_classifier import IntentClassifier
from baf.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from baf.nlp.ner.ner_prediction import NERPrediction
from baf.nlp.preprocessing.text_preprocessing import process_text, tokenize

from collections import Counter

if TYPE_CHECKING:
    from baf.core.state import State
    from baf.nlp.nlp_engine import NLPEngine

try:
    import torch
    import torch.optim as optim
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
except ImportError:
    logger.warning("torch dependencies in SimpleIntentClassifierTorch could not be imported. You can install them from the "
                   "requirements/requirements-torch.txt file")

try:
    from sklearn.preprocessing import LabelEncoder
except ImportError:
    logger.warning("scikit-learn dependencies in SimpleIntentClassifierTorch could not be imported. You can install them from the "
                   "requirements/requirements-extras.txt file")


class TextClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, pad_idx, activation_last_layer):
        super(TextClassifier, self).__init__()
        self.activation_last_layer: str = activation_last_layer
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.pooling = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.embedding(x)
        x = x.permute(0, 2, 1)  # Change dimension order for pooling
        x = self.pooling(x).squeeze(2)  # Apply pooling
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        if self.activation_last_layer == 'softmax':
            # sum of outputs == 1
            x = torch.softmax(self.fc3(x), dim=1)
        elif self.activation_last_layer == 'sigmoid':
            x = torch.sigmoid(self.fc3(x))
        return x


class TextDataset(Dataset):

    def __init__(self, texts, labels, vocab, max_len, language):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len
        self.language = language

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        # Tokenize and pad text
        tokens = tokenize(text, self.language)
        tokens = [self.vocab.get(token, self.vocab[SimpleIntentClassifierTorch.UNK]) for token in tokens]
        tokens = tokens[:self.max_len] + [self.vocab[SimpleIntentClassifierTorch.PAD]] * (self.max_len - len(tokens))

        return torch.tensor(tokens, dtype=torch.long), torch.tensor(label, dtype=torch.long)


class SimpleIntentClassifierTorch(IntentClassifier):
    """A Simple Pytorch-based Intent Classifier.

    It works using a simple Neural Network (the prediction model) for text classification.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        state (State): the state the intent classifier belongs to

    Attributes:
        _model (`torch.nn.Module <https://pytorch.org/docs/stable/generated/torch.nn.Module>`_):
            The intent classifier language model

    See Also:
        :class:`~baf.nlp.intent_classifier.intent_classifier_configuration.SimpleIntentClassifierConfiguration`.
    """

    UNK = '<UNK>'
    PAD = '<PAD>'

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: 'State'
    ):
        super().__init__(nlp_engine, state)

        self.__total_training_sentences: list[str] = []
        """All the processed training sentences of all intents of the intent classifier's state."""

        self.__total_training_sequences: list[list[int]] = []
        """All the training sequences of all intents of the intent classifier's state."""

        self.__total_labels: list[int] = []
        """The label (identifying the intent) of all training sentences."""

        self.__total_labels_encoded: list[int] = []
        """The encoded label of all training sentences."""

        self.__intent_label_mapping: dict[int, Intent] = {}
        """A mapping of the intent labels and their corresponding intents."""

        self.__vocab: dict[str, int] = {}
        """The vocabulary of the intent classifier (i.e., all known tokens)."""

        for intent in self._state.intents:
            intent.process_training_sentences(self._nlp_engine)
            index_intent = self._state.intents.index(intent)
            self.__total_training_sentences.extend(
                intent.processed_training_sentences
            )
            self.__total_labels.extend(
                [index_intent for _ in range(len(intent.processed_training_sentences))]
            )
            self.__intent_label_mapping[index_intent] = intent

        # Preprocessing
        le = LabelEncoder()
        self.__total_labels_encoded = le.fit_transform(self.__total_labels)
        language: str = self._nlp_engine.get_property(nlp.NLP_LANGUAGE)
        all_tokens = [token for text in self.__total_training_sentences for token in tokenize(text, language)]
        self.__vocab = {word: idx for idx, (word, _) in enumerate(Counter(all_tokens).items(), 1)}
        self.__vocab[SimpleIntentClassifierTorch.PAD] = 0
        self.__vocab[SimpleIntentClassifierTorch.UNK] = len(self.__vocab)
        for training_sentence in self.__total_training_sentences:
            self.__total_training_sequences.append([
                self.__vocab.get(token, self.__vocab[SimpleIntentClassifierTorch.UNK])
                for token in tokenize(training_sentence, language)
            ])

        # Model Initialization
        self._model = TextClassifier(
            vocab_size=len(self.__vocab),
            embed_dim=self._state.ic_config.embedding_dim,
            hidden_dim=self._state.ic_config.hidden_dim,
            output_dim=len(set(self.__total_labels_encoded)),
            pad_idx=self.__vocab[SimpleIntentClassifierTorch.PAD],
            activation_last_layer=self._state.ic_config.activation_last_layer
        )

    def train(self) -> None:
        # Dataset and DataLoader
        dataset = TextDataset(
            self.__total_training_sentences,
            self.__total_labels_encoded,
            self.__vocab,
            self._state.ic_config.input_max_num_tokens,
            self._nlp_engine.get_property(nlp.NLP_LANGUAGE)
        )
        dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self._model.parameters(), lr=self._state.ic_config.lr)

        self._model.train()
        for epoch in range(self._state.ic_config.num_epochs):
            total_loss = 0
            for texts, labels in dataloader:
                optimizer.zero_grad()
                outputs = self._model(texts)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            # logger.info(f"Epoch {epoch + 1}/{self._state.ic_config.num_epochs}, Loss: {total_loss / len(dataloader):.4f}")

    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        message = process_text(message, self._nlp_engine)
        intent_classifier_results: list[IntentClassifierPrediction] = []
        language: str = self._nlp_engine.get_property(nlp.NLP_LANGUAGE)

        # We try to replace all potential entity value with the corresponding entity name
        ner_prediction: NERPrediction = self._state.agent.nlp_engine.ner.predict(self._state, message)
        for (ner_sentence, intents) in ner_prediction.ner_sentences.items():
            run_full_prediction: bool = True
            self._model.eval()
            tokens = tokenize(message, language)
            tokens = [self.__vocab.get(token, self.__vocab[SimpleIntentClassifierTorch.UNK]) for token in tokens]
            tokens = tokens[:self._state.ic_config.input_max_num_tokens]

            if self._state.ic_config.discard_oov_sentences and all(token == self.__vocab[SimpleIntentClassifierTorch.UNK] for token in tokens):
                # The sentence to predict consists of only out of vocabulary tokens,
                # so we can automatically assign a zero probability to all classes
                prediction = np.zeros(len(self._state.intents))
                run_full_prediction = False  # no need to go ahead with the full NN-based prediction
            elif self._state.ic_config.check_exact_prediction_match:
                # We check if there is an exact match with one of the training sentences
                for i, training_sequence in enumerate(self.__total_training_sequences):
                    intent_label = self.__total_labels[i]
                    if np.array_equal(tokens, training_sequence) \
                            and self.__intent_label_mapping[intent_label] in intents:
                        run_full_prediction = False
                        # We set to 1 the corresponding intent with full confidence and to zero all the
                        prediction = np.zeros(len(self._state.intents))
                        np.put(prediction, intent_label, 1.0, mode='raise')
                        # We don't check if there is more than one intent that could be the exact match
                        # as this would be an inconsistency in the agent definition anyway
                        break

            if run_full_prediction:
                tokens = tokens + [self.__vocab[SimpleIntentClassifierTorch.PAD]] * (self._state.ic_config.input_max_num_tokens - len(tokens))
                input_tensor = torch.tensor(tokens, dtype=torch.long).unsqueeze(0)
                with torch.no_grad():
                    output = self._model(input_tensor)
                    prediction = output.squeeze().tolist()
                    if isinstance(prediction, float):
                        prediction = [prediction]

            for intent in intents:
                # It is impossible to have a duplicated intent in another ner_sentence
                intent_index = self._state.intents.index(intent)
                intent_classifier_results.append(IntentClassifierPrediction(
                    intent,
                    prediction[intent_index],
                    ner_sentence,
                    ner_prediction.intent_matched_parameters[intent]
                ))

        return intent_classifier_results
