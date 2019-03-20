from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from tqdm import tqdm
from nltk import FreqDist, bigrams
from bggdb import BoardGame, Process, TitleLetterPairBigram
from toolkit import get_config
# Load configuration
config_file_name = 'config.json'
config_options = get_config(config_file_name)

# Initialize database session
sa_engine = create_engine(config_options['db_url'], pool_recycle=3600)
session = Session(bind=sa_engine)
maximum_games_to_process = 4000

# Get a game title to process
for single_game in tqdm(
        session.query(BoardGame.id, BoardGame.name, Process.title_letterpair_bigram).
        join(Process, isouter=True).
        filter(or_(Process.title_letterpair_bigram == 0, Process.title_letterpair_bigram.is_(None))).
        limit(maximum_games_to_process),
        desc='Building n-grams',
        total=maximum_games_to_process):

    # Pad the game name with spaces. Help set word boundaries
    pre_chopped_name = " {} ".format(single_game.name)
    # Build the frequency distribution of letter pair bigrams in a title
    bigram_frequency_distribution = FreqDist(bigrams(["".join(pair) for pair in list(zip(pre_chopped_name, pre_chopped_name[1:]))]))

    # Process each individually to determine if we are updating existing or adding new
    for single_bigram, frequency in bigram_frequency_distribution.items():
        try:
            # Check if bigram is already known in database
            known_bigram = None
            known_bigram = session.query(TitleLetterPairBigram).filter(TitleLetterPairBigram.first == single_bigram[0], TitleLetterPairBigram.second == single_bigram[1]).first()
        except NoResultFound:
            pass

        if known_bigram is not None:
            known_bigram.add_frequency(frequency)
        else:
            session.add(TitleLetterPairBigram(first=single_bigram[0], second=single_bigram[1], frequency=frequency))

    # Set the processed bit for this game
    if single_game.title_letterpair_bigram is None:
        # This game does not exist in the process table and needs to be added.
        session.add(Process(game_id=single_game.id, title_letterpair_bigram=1))
    else:
        # This game does exist and needs to be flagged as complete when done.
        session.query(Process).filter(Process.game_id == single_game.id).update({'title_letterpair_bigram': 1})

    session.commit()
