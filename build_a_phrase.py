from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sacremoses import MosesDetokenizer
from random import choices
from bggdb import DescriptionWordBigram

# Create a MariaDB database session
sa_engine = create_engine('mysql+pymysql://bgg:it6jTeIN6sNldnJvMm3R@localhost:49000/boardgamegeek?charset=utf8mb4', pool_recycle=3600)
session = Session(bind=sa_engine)

# Using the starting word start a markov chain
end_of_sentence_punctuation = ['.', '?', '!']
max_token_chain = 40
token_index = 1
tokens = []
md = MosesDetokenizer()

# Get the first word in the sentence
current_word = choices([row.second for row in session.query(DescriptionWordBigram.second).filter(DescriptionWordBigram.first.in_(end_of_sentence_punctuation)).all()])[0]

while token_index <= max_token_chain:
    try:
        # Add the current word to the list
        tokens.append(current_word)
        # Get the selection of potential words
        next_tokens = session.query(DescriptionWordBigram).filter(DescriptionWordBigram.first == current_word).all()
        # Build two tuples of equal elements words and weights
        words_with_frequencies = tuple(zip(*([[t.second, t.frequency] for t in next_tokens])))
        # Get the next word using markov chains
        current_word = choices(words_with_frequencies[0], weights=words_with_frequencies[1])[0]
    except NoResultFound as e:
        # There was nothing found to follow the word so lets just end the loop
        token_index = max_token_chain
    if current_word in end_of_sentence_punctuation:
        token_index = max_token_chain
        tokens.append(current_word)

    token_index += 1

print(md.detokenize(map(str, tokens)))
