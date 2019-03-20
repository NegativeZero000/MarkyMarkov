from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import func
from random import choices
from bggdb import TitleLetterPairBigram
from toolkit import get_config

# Load configuration
config_file_name = 'config.json'
config_options = get_config(config_file_name)

# Initialize database session
sa_engine = create_engine(config_options['db_url'], pool_recycle=3600)
session = Session(bind=sa_engine)

def build_markov_title(
        session,
        minimum_title_length,
        word_length_threshold=7,
        end_of_word_bias_factor=0.1,
        word_boundary_characters=[' '],
        start_of_title_characters_to_ignore=['(', '"', '¿', '*', "'"],
        start_of_word_characters_to_ignore=[]):
    '''
    This routine will build a title or small phrase using markov chains and the letter pair database of bigrams.

    session                                 A bound SQLAlchmey session
    minimum_title_length                    Title will need to be as least this many characters long. It will not cut of incomplete words
    word_length_threshold                   Once the threshold is passed the chains will be biased towards ending the word quicker. Compounds for every letter passed this threshold
    end_of_word_bias_factor                 Percentage of increased frequency given to end of word characters
    word_boundary_characters                Characters used to define the start of a word. Usually a space
    start_of_title_characters_to_ignore     Start of words characters not to use for the start of a title
    start_of_word_characters_to_ignore      Start of words characters not to use for the start of words

    '''

    title_tokens = []                      # Storage location for the bigram tokens

    # Get the start of this title
    current_letter_pair = choices([row.first for row in session.query(
        TitleLetterPairBigram.first).filter(
            (func.LEFT(TitleLetterPairBigram.first, 1)).in_(word_boundary_characters),
            (func.RIGHT(TitleLetterPairBigram.first, 1)).notin_(start_of_title_characters_to_ignore)
    ).all()])[0]

    # Append the second character to the title
    title_tokens.append(current_letter_pair[1])

    # Continue building words/ the title until all condition are met
    while(True):
        # Get the next token in the markov chain
        next_tokens = session.query(TitleLetterPairBigram).filter(TitleLetterPairBigram.first == current_letter_pair, TitleLetterPairBigram.first.notin_(start_of_word_characters_to_ignore)).all()

        # Check if there are any potential tokens after current_letter_pair
        if len(next_tokens) > 0:
            # Choose the next token. Evaulate any ancillary conditions first
            title_thus_far = "".join(title_tokens)
            if len(title_thus_far[title_thus_far.rfind(" ") + 1:]) >= word_length_threshold:
                # This word is getting long
                total_bigram_freqeuncy = sum(list(single_bigram.frequency for single_bigram in next_tokens))
                # Bias the frequency of end word pair
                for single_bigram in next_tokens:
                    if single_bigram.second[0] == " ":
                        single_bigram.frequency = single_bigram.frequency + (total_bigram_freqeuncy * end_of_word_bias_factor * (len(title_thus_far) - word_length_threshold + 1))

            # Build two tuples of equal elements words and weights
            pairs_with_frequencies = tuple(zip(*([[t.second, t.frequency] for t in next_tokens])))

            # Get the next word with markov
            current_letter_pair = choices(pairs_with_frequencies[0], weights=pairs_with_frequencies[1])[0]

            # Add the current letter, from the pair, to the list
            title_tokens.append(current_letter_pair[1])

            # Clean flags where appropriate and see if we are done the title yet.
            if current_letter_pair[1] == " ":
                # Check if we have exceeded the minimum title length.
                if len(title_tokens) >= minimum_title_length:
                    break
        else:
            # No tokens available.
            if len(title_tokens) >= minimum_title_length:
                break
            else:
                # Title is not long enough. End the word and start a new one.
                title_tokens.append(" ")
                # Get the start of this word
                current_letter_pair = choices([row.first for row in session.query(
                    TitleLetterPairBigram.first).filter(
                        (func.LEFT(TitleLetterPairBigram.first, 1)).in_(word_boundary_characters),
                        (func.RIGHT(TitleLetterPairBigram.first, 1)).notin_(start_of_title_characters_to_ignore)
                ).all()])[0]
                # Append the second character to the title
                title_tokens.append(current_letter_pair[1])

    return "".join(title_tokens)

# Test the efficiency of the end_of_word_bias_factor when making titles


for i in range(9):
    print(build_markov_title(session=session, minimum_title_length=15, word_length_threshold=4))
