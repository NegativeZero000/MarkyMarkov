from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sacremoses import MosesDetokenizer
from random import choices, choice
from bggdb import DescriptionWordBigram
from toolkit import get_config
from argparse import ArgumentParser, ArgumentTypeError

def check_positive(value):
    error = ArgumentTypeError("{} is not an integer greater than 0.".format(value))

    try:
        ivalue = int(value)
    except ValueError:
        raise error

    if ivalue < 0:
        raise error
    return ivalue

class TokenPair:
    '''Character set pairs and associated values to influence choices involving members'''
    __slots__ = 'token', 'pair', '__base_bias', '__bias_adjust', '__current_bias', '__word_count'

    def __init__(self, token, pair, base_bias=0.5, bias_adjust=0.1):
        self.token = token
        self.pair = pair
        self.base_bias = base_bias
        self.bias_adjust = bias_adjust
        self.current_bias = base_bias
        self.__word_count = 0

    def is_order_dependant(self):
        return self.token == self.pair

    def raise_bias(self):
        self.current_bias += self.bias_adjust

    @property
    def word_count(self):
        return self.__word_count

    @property
    def base_bias(self):
        return self.__base_bias

    @base_bias.setter
    def base_bias(self, base_bias):
        if base_bias < 0:
            self.__base_bias = 0
        elif base_bias > 1:
            self.__base_bias = 1
        else:
            self.__base_bias = base_bias

    @property
    def bias_adjust(self):
        return self.__bias_adjust

    @bias_adjust.setter
    def bias_adjust(self, bias_adjust):
        if bias_adjust < 0:
            self.__bias_adjust = 0
        elif bias_adjust > 1:
            self.__bias_adjust = 1
        else:
            self.__bias_adjust = bias_adjust

    @property
    def current_bias(self):
        return self.__current_bias

    @current_bias.setter
    def current_bias(self, current_bias):
        if current_bias < 0:
            self.__current_bias = 0
        elif current_bias > 1:
            self.__current_bias = 1
        else:
            self.__current_bias = current_bias

    def __repr__(self):
        return "<CharacterPair(token='{}', pair='{}', base_bias={}, bias_adjust={}, current_bias={}>".format(
            self.token, self.pair, self.__base_bias, self.__bias_adjust, self.__current_bias
        )

def adjust_frequency(
        tokens,
        known_token_pairs=[],
        active_token_pair=None):
    '''
    Varying conditions can adjust the normal weight of words. Cycle through and adjust accordingly. If a character pair is encountered

    tokens                                  2 member nested list where the first is a list of words. Second in weights used in choice
    active_token_pair                       The active TokenPair used to influence/bias frequencies in its favour.
    known_token_pairs                       Complete list of known TokenPair's. Used to remove the matching pair of order dependant tokens
    '''

    # print('Number of passed token pairs: {}'.format(len(token_pairs)))
    # print('Live token pair: {}'.format(token_pairs[0]))

    # if(len(triggered_token_pairs) > 0 and triggered_token_pairs[0].pair in words_with_frequencies[0]):

    # Remove any order dependant pairs from the tokens list if we are not currently searching for that pair
    print('Active token pair: {}'.format(active_token_pair))
    banned_tokens = [tp.pair for tp in known_token_pairs if tp.pair != active_token_pair.pair]
    print(banned_tokens)
    for token in tokens:
        if token[0] in banned_tokens:
            # This token needs its weight removed to prevent it from being selected
            token[1] = 0

    # If there is a token pair active we need to change the weights of the pair if found.
    if active_token_pair is not None:
        # Transpose the list into word weight pairs.
        # tokens = list(map(list, zip(*tokens)))

        # Using the first in line token pairs adjust the weights
        # Get the total sum of all weights
        # print("The tokens", tokens)
        # print([t[1] for t in tokens])

        # Determine the weight that will need to be distributed among the found pairs
        total_weight = sum([t[1] for t in tokens])
        total_pairs = tokens[0].count(active_token_pair.pair)

        # Adjust the weights assuming there is even any to adjust
        if total_pairs > 0:
            weight_to_distrubute = (active_token_pair.current_bias * total_weight) / total_pairs

            for token in tokens:
                if token[0] == active_token_pair.pair:
                    token[1] = weight_to_distrubute

    # Return the tokens regardless if edits were completed
    return tokens

# Process command line arguments
parser = ArgumentParser(description='Create sentence(s) based on bi-grams')
parser.add_argument('--config', type=str, default='config.json', help='Config file name in script directory')
parser.add_argument('--sentencecount', type=check_positive, default=2, help='Number of sentences to generate')
parser.add_argument('--terminators', '--term', type=str, default='.?!', help='String of end-of-sentence characters')
arguments = parser.parse_args()

# Load configuration
config_options = get_config(arguments.config)

# Initialize database session
sa_engine = create_engine(config_options['db_url'], pool_recycle=3600)
session = Session(bind=sa_engine)

# Prepare phrase special charaters and flags
end_of_sentence_punctuation = list(arguments.terminators)
sentence_index = 0
tokens = []
detokenizer = MosesDetokenizer()
destiny_pairs = [
    TokenPair(token='(', pair=')'),
    TokenPair(token='\'', pair='\''),
    TokenPair(token='"', pair='"')
]
triggered_token_pairs = []

# Get the first word in the sentence by selecting a bigram use end of sentence punctuation
current_token = choices([row.second for row in session.query(DescriptionWordBigram.second).filter(DescriptionWordBigram.first.in_(end_of_sentence_punctuation)).all()])[0]
current_token = 'Abacus'

# Continue to make sentences until the count is met
while sentence_index < arguments.sentencecount:

    # Add the current word to the list
    tokens.append(current_token)

    # Check to see if the current token is in the mating list
    token_pair = next((tp for tp in destiny_pairs if tp.token == current_token), None)

    if(token_pair is not None):
        # Push any existing elements down. Prioritize most recent finding.
        triggered_token_pairs.insert(0, token_pair)

    try:
        # Get the selection of potential next tokens
        next_tokens = session.query(DescriptionWordBigram).filter(DescriptionWordBigram.first == current_token).all()

        # Build two lists of equal elements: words and weights
        # words_with_frequencies = [[t.second, t.frequency] for t in next_tokens]

        # words_with_frequencies = [list(group) for group in zip(*([[t.second, t.frequency] for t in next_tokens]))]

        # Adjust the words/token respective weights where required. Primarily based son the presense of destiny pairs.
        words_with_frequencies = adjust_frequency(
            tokens=[[t.second, t.frequency] for t in next_tokens],
            active_token_pair=next(iter(triggered_token_pairs), None),
            known_token_pairs=destiny_pairs
        )
        # print('Number of token pairs: {}'.format(len(triggered_token_pairs)))
        # print('Current pair to bias: {}'.format(triggered_token_pairs[0].pair if len(triggered_token_pairs) > 0 else 0))
        # print('Found in word set?: {}'.format(triggered_token_pairs[0].pair in words_with_frequencies[0] if len(triggered_token_pairs) > 0 else 0))

        # Get the next word using markov chains. First transpose the words_with_frequencies
        words_with_frequencies = list(map(list, zip(*words_with_frequencies)))

        current_token = choices(words_with_frequencies[0], weights=words_with_frequencies[1])[0]

        # If there is a triggered token pair see if its been resolved
        if len(triggered_token_pairs) > 0:
            if triggered_token_pairs[0].pair == current_token:
                # The current token satisfies the pair and can be removed
                del triggered_token_pairs[0]
            else:
                # The active triggered token pair is still unmatched. Adjust bias
                triggered_token_pairs[0].raise_bias()

    except NoResultFound:
        # There was nothing found to follow the word so lets just end the sentence
        current_token = choice(end_of_sentence_punctuation)

    if current_token in end_of_sentence_punctuation:
        sentence_index = sentence_index + 1

tokens.append(current_token)
print(detokenizer.detokenize(map(str, tokens)))
