from typing import TYPE_CHECKING

from besser.bot.core.entity.entity_entry import EntityEntry
from besser.bot.nlp.preprocessing.text_preprocessing import process_text

if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine


class Entity:
    """The Entity core component of a bot.

    Entities are used to specify the type of information to extract from user inputs. These entities are embedded in
    intent parameters.

    Args:
        name (str): the entity's name
        base_entity (bool): weather the entity is base or not (i.e. custom)
        entries (dict[str, list[str]] or None): the entity entries. If base_entity, there are no entries (i.e. None)

    Attributes:
        name (str): The entity's name
        bool (base_entity): Weather the entity is base or not (i.e. custom)
        entries (list[EntityEntry] or None): The entity entries. If base_entity, there are no entries (i.e. None)
    """

    def __init__(
            self,
            name: str,
            base_entity: bool = False,
            entries: dict[str, list[str]] or None = None
    ):
        if entries is None:
            entries = {}
        self.name: str = name
        self.base_entity: bool = base_entity
        self.entries: list[EntityEntry] or None
        if self.base_entity:
            self.entries = None
        else:
            self.entries = []
            for value, synonyms in entries.items():
                self.entries.append(EntityEntry(value, synonyms))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def process_entity_entries(self, nlp_engine: 'NLPEngine') -> None:
        """Process the entity entries.

        Args:
            nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot
        """
        if not self.base_entity:
            for entry in self.entries:
                entry.processed_value = process_text(entry.value, nlp_engine)
                entry.processed_synonyms = []
                for synonym in entry.synonyms:
                    entry.processed_synonyms.append(process_text(synonym, nlp_engine))
