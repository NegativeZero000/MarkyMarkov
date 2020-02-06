from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sacremoses import MosesDetokenizer
from random import choices
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

parser = ArgumentParser(description='Process a number of stored games for bi-grams')
parser.add_argument('--maxtokens', type=str, default=40, help='Maximum number of tokens to use.')
parser.add_argument('--config', type=str, default='config.json', help='Config file name')
parser.add_argument('--stctrm', type=str, default='.?!', help='List of send of sentence characters')
arguments = parser.parse_args()

# Load configuration
config_options = get_config(arguments.config)

# Initialize database session
sa_engine = create_engine(config_options['db_url'], pool_recycle=3600)
session = Session(bind=sa_engine)

# Using the starting word start a markov chain
end_of_sentence_punctuation = list(arguments.stctrm)
token_index = 1
tokens = []
detokenizer = MosesDetokenizer()

# Get the first word in the sentence by selecting a bigram use end of sentence punctuation
current_word = choices([row.second for row in session.query(DescriptionWordBigram.second).filter(DescriptionWordBigram.first.in_(end_of_sentence_punctuation)).all()])[0]

while token_index <= arguments.maxtokens:
    try:
        # Add the current word to the list
        tokens.append(current_word)
        # Get the selection of potential words
        next_tokens = session.query(DescriptionWordBigram).filter(DescriptionWordBigram.first == current_word).all()
        # Build two tuples of equal elements words and weights
        words_with_frequencies = tuple(zip(*([[t.second, t.frequency] for t in next_tokens])))
        # Get the next word using markov chains
        current_word = choices(words_with_frequencies[0], weights=words_with_frequencies[1])[0]
    except NoResultFound:
        # There was nothing found to follow the word so lets just end the loop
        token_index = arguments.maxtokens

    if current_word in end_of_sentence_punctuation:
        token_index = arguments.maxtokens
        tokens.append(current_word)

    token_index += 1

print(detokenizer.detokenize(map(str, tokens)))
