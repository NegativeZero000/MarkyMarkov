import requests
import xml.etree.ElementTree as etree
from time import sleep
from html import unescape
from tqdm import tqdm
from urllib.parse import urlencode

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError
from bggdb import BoardGame

sa_engine = create_engine('mysql+pymysql://bgg:it6jTeIN6sNldnJvMm3R@localhost:49000/boardgamegeek?charset=utf8mb4', pool_recycle=3600)
session = Session(bind=sa_engine)
# Base.metadata.create_all(sa_engine)

# Get the collection of board games from board game geeek
boardgamegeek_xml_api_url = 'http://www.boardgamegeek.com/xmlapi2/thing'
# board_game_ids = [1234, 46564, 65464]

# Figure out where we need to start from based on last know ID in database
last_game_id = session.query(func.max(BoardGame.id)).scalar()
simultaneous_id_request = 8
bgg_id_check_passes = 800
max_ids_to_query = simultaneous_id_request * bgg_id_check_passes

for game_index in tqdm(range(last_game_id + 1, last_game_id + max_ids_to_query + 1, simultaneous_id_request), desc="Gathering games", total=bgg_id_check_passes):
    # Generate 'simultaneous_id_request' ids for this pass.
    board_game_ids = ",".join(map(str, range(game_index, game_index + simultaneous_id_request)))
    bgg_api_parameters = {
        'type': 'boardgame',
        'id': board_game_ids
    }
    # print(f"Parameters Used: {bgg_api_parameters}")
    # Call the BGG API
    api_url = '{}?{}'.format(boardgamegeek_xml_api_url, urlencode(bgg_api_parameters, safe=","))
    # print(f'Using url: {api_url}')

    bgg_response = requests.get(url=api_url)

    if bgg_response.status_code == 200:
        # Convert the feed into an Element object
        boardgames = etree.fromstring(bgg_response.content)
        # valid_ids = []

        # Work with each board game individually assuming more than one was returned
        for boardgame in boardgames.getchildren():
            found_description = boardgame.find('description').text

            # There are some games that have no description. Filter those out.
            if type(found_description) is None.__class__:
                print("\n{} has no description".format(boardgame.attrib['id']))
            else:
                # print('Valid boardgame found: {}. Description Length: {}'.format(
                #     boardgame.attrib['id'],
                #     len(found_description)
                # ))

                session.add(BoardGame(
                    id=boardgame.attrib['id'],
                    name=boardgame.find('.//name[@type="primary"]').get('value'),
                    description=unescape(found_description)
                ))
                # valid_ids.append(boardgame.attrib['id'])

        # print("\nValid ID's proccessed: {}".format(", ".join(map(str, valid_ids))))
    else:
        print(f'{api_url} triggered {bgg_response.status_code}')

    # session.rollback()
    try:
        session.commit()
    except DataError as e:
        print(e)
    # Put in a limiter to prevent frequent requests to the site.
    sleep(5)
