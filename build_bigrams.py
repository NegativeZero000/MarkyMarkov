from nltk import word_tokenize, bigrams, FreqDist
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound
from tqdm import tqdm
from bggdb import BoardGame, Process, DescriptionWordBigram
from toolkit import get_config
from argparse import ArgumentParser, ArgumentTypeError  # https://docs.python.org/3.3/library/argparse.html

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
parser.add_argument('--number', type=check_positive, default=20, help='Number of games to process for bi-grams')
parser.add_argument('--config', type=str, default='config.json', help='Path to config')
arguments = parser.parse_args()

# Load configuration
config_options = get_config(arguments.config)

# Initialize database session
sa_engine = create_engine(config_options['db_url'], pool_recycle=3600)
session = Session(bind=sa_engine)

for single_game in tqdm(
        session.query(BoardGame.id, BoardGame.description, Process.description_word_bigram).
        join(Process, isouter=True).
        filter(or_(Process.description_word_bigram == 0, Process.description_word_bigram.is_(None))).
        limit(arguments.number),
        desc='Building n-grams',
        total=arguments.number):

    # Harvest bigrams from this games decription and add them to the table
    bigram_frequency_distribution = FreqDist(bigrams(word_tokenize(single_game.description)))
    # https://stackoverflow.com/questions/32185072/nltk-word-tokenize-behaviour-for-double-quotation-marks-is-confusing
    # Process each bigram. If new, add it to the db else adjust its frequency
    for single_bigram, frequency in bigram_frequency_distribution.items():
        try:
            # Check if bigram is already known in database
            known_bigram = None
            known_bigram = session.query(DescriptionWordBigram).filter(DescriptionWordBigram.first == single_bigram[0], DescriptionWordBigram.second == single_bigram[1]).first()
        except NoResultFound:
            pass

        if known_bigram is not None:
            known_bigram.add_frequency(frequency)
        else:
            session.add(DescriptionWordBigram(first=single_bigram[0], second=single_bigram[1], frequency=frequency))

    # Set the processed bit for this game
    if single_game.description_word_bigram is None:
        # This game does not exist in the process table and needs to be added.
        session.add(Process(game_id=single_game.id, description_word_bigram=1))
    else:
        # This game does exist and needs to be flagged as complete when done.
        session.query(Process).filter(Process.game_id == single_game.id).update({'description_word_bigram': 1})

    session.commit()
