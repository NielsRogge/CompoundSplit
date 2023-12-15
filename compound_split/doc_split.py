#!/usr/bin/python3
# Copyright eBrevia.com 2019
"""Document-level splitting module."""

import logging
import re
import sys
import pkgutil

from compound_split import doc_config
from compound_split import char_split

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DE_LETTER = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
             'abcdefghijklmnopqrstuvwxyz' +
             'ÄÖÜäöüß')
DE_WORD_PAT = re.compile(r'\b[%s]+\b' % (DE_LETTER))
GLUES = ['ens', 'en', 'er', 'es', 'e', 'n', 's']
MIDDLE_DOT = '\N{MIDDLE DOT}'

# Caches
KNOWN_WORDS = set()
ALREADY_SPLIT_WORDS = {}


def find_root(word):
    """Looks in KNOWN_WORDS; if that fails, peels off German compound glue.
       If nothing works, return None.
    """
    if word in KNOWN_WORDS:
        return word
    # might not actually be a noun
    not_noun = word.lower()
    if not_noun in KNOWN_WORDS:
        return not_noun
    # do glue processing
    for glue in GLUES:
        if word.endswith(glue):
            root_length = len(word) - len(glue)
            root = word[:root_length]
            if root in KNOWN_WORDS:
                return word
    return None


def get_best_split(word):
    """First look up the word, and if found, return it.
       Then get the best available split of a word into 2 words.
       If score of best is less than 0, no split is available.
       If no split is available, the two words are the same; return one.
    """
    root = find_root(word)
    if root:
        return [root]
    candidate = char_split.split_compound(word)[0]
    if candidate[0] <= 0:
        return [word]
    if candidate[1] == candidate[2]:
        return [candidate[1]]
    return [candidate[1], candidate[2]]


def maximal_split(word, de_dict=doc_config.DEFAULT_DICT):
    """Recursively split a single word into a list of words.
       Only the first result is split further, as CharSplit divides
       compounds into non-final and final parts.
       Try to avoid splitting words other than nouns,
       as false positives are too likely.
    """
    # This is an entry point, so load the dictionary just in case.
    load_known_words(de_dict)
    # Do not split a non-noun
    if not word[0].isupper():
        return [word]
    word_list = get_best_split(word)
    # Binary splitter was unable to split
    if len(word_list) == 1:
        return word_list
    # If split product is too short, ignore the split
    if len(word_list[0]) < 4 or len(word_list[1]) < 4:
        return [word]
    # Recursively split the non-head and prepend it to the head
    return maximal_split(word_list[0]) + [word_list[1]]


def load_known_words(de_dict=doc_config.DEFAULT_DICT, de_misc=True):
    """Load the dictionary into KNOWN_WORDS."""
    if KNOWN_WORDS:
        return  # already loaded
    if de_dict is None:
        de_dict = doc_config.DEFAULT_DICT
    load_dict(de_dict)
    # if de_misc:
    #     load_dict(doc_config.DE_MISC_DICT)
    # print('%d known words loaded\n' % (len(KNOWN_WORDS)), file=sys.stderr)
    logger.info('%d known words loaded', len(KNOWN_WORDS))


def load_dict(dict_path):
    data = open(dict_path, 'rb').read()
    data = data.decode('utf-8')
    words = data.split("\n")
    for word in words:
        if not (word == '' or word.startswith('#')):
            KNOWN_WORDS.add(word.strip())


def maximal_split_str(word, de_dict=None):
    """Maximally split a word and return it with middle dots."""
    # This is an entry point, so load the dictionary just in case.
    load_known_words(de_dict)
    # if memoized, don't split
    try:
        return ALREADY_SPLIT_WORDS[word]
    except KeyError:
        pass
    upper_case = word[0].isupper()
    result_list = [w.lower() for w in maximal_split(word)]
    result_str = MIDDLE_DOT.join(result_list)
    if upper_case:
        result0 = result_str[0].upper()
    else:
        result0 = result_str[0]
    result = result0 + result_str[1:]
    ALREADY_SPLIT_WORDS[word] = result
    return result


def add_additional_known_words(additional_known_words):
    """Add additional known words added by the user"""
    if additional_known_words is not None:
        if not isinstance(additional_known_words, list):
            raise ValueError(
                f"additional_knwon_words should be of type list and not of type {type(additional_known_words)}")
        for word in additional_known_words:
            if not word == '':
                KNOWN_WORDS.add(word)


def doc_split(doc, de_dict=None, result_map=None, additional_known_words=None):
    """Split a whole document (a string) using the specified dictionary.
       Return the whole document with splitting dots.
    """
    if doc == '':
        return ''
    # This is an entry point, so load the dictionary just in case.
    load_known_words(de_dict)
    add_additional_known_words(additional_known_words)
    result = []
    if result_map is not None:
        result_map.clear()
    windexes = [(mobj.start(), mobj.end()) for mobj in DE_WORD_PAT.finditer(doc)]
    # Non-word before the first word (OK if empty)
    result.append(doc[:windexes[0][0]])
    # pylint: disable=consider-using-enumerate
    for i in range(0, len(windexes)):
        # Add a split word and the following non-word (OK if empty)
        (start, end) = windexes[i]
        unsplit_word = doc[start:end]
        split_word = maximal_split_str(unsplit_word)
        result.append(split_word)
        if result_map is not None and MIDDLE_DOT in split_word:
            result_map[unsplit_word] = split_word
        if i == len(windexes) - 1:
            next_start = len(doc)
        else:
            next_start = windexes[i + 1][0]
        result.append(doc[end:next_start])
    return ''.join(result)  # TODO also return all splitted words for easy checking


def main():
    """Read whole document from stdin, output in maximally split format.
       Usage: ./doc_split.py dict
    """
    if len(sys.argv) > 1:
        de_dict = sys.argv[1]
    else:
        de_dict = doc_config.DEFAULT_DICT
    input_str = sys.stdin.read()
    output_str = doc_split(input_str, de_dict)
    sys.stdout.write(output_str)


if __name__ == "__main__":
    main()
