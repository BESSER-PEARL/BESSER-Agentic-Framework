import nltk
import snowballstemmer

from besser.agent.exceptions.logger import logger

lang_map_tokenizers = nltk.SnowballStemmer.languages
lang_map = {
    'en': 'english',
    'es': 'spanish',
    'fr': 'french',
    'it': 'italian',
    'de': 'german',
    'nl': 'dutch',
    'pt': 'portuguese',
    'ca': 'catalan',
    # TODO: replace german stemmer by actual luxembourgish stemmer
    'lb': 'luxembourgish'
}
stemmers: dict[str, snowballstemmer.stemmer] = {}

for nltk_tokenizer in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{nltk_tokenizer}')
    except LookupError:
        nltk.download(nltk_tokenizer)


def create_or_get_stemmer(lang: str = 'english') -> snowballstemmer:
    if lang in stemmers:
        return stemmers[lang]
    stemmer = snowballstemmer.stemmer(lang)
    stemmers[lang] = stemmer
    logger.info(f'Stemmer added: {lang}')
    return stemmer
