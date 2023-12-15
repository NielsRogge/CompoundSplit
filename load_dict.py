import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

KNOWN_WORDS = set()

def load_known_words(dict_path):
    """Load the dictionary into KNOWN_WORDS."""
    if KNOWN_WORDS:
        return  # already loaded
    load_dict(dict_path)
    logger.info('%d known words loaded', len(KNOWN_WORDS))


def load_dict(dict_path):
    data = open(dict_path, 'rb').read()
    data = data.decode('utf-8')
    words = data.split("\n")
    for word in words:
        if not (word == '' or word.startswith('#')):
            KNOWN_WORDS.add(word.strip())

    print("Known words:", KNOWN_WORDS)
    print("Number of words:", len(KNOWN_WORDS))

if __name__ == "__main__":
    load_known_words("/Users/nielsrogge/Documents/python_projects/CompoundSplit/compound_split/dicts/nl-NL.dic")