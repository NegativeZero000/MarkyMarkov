# Marky Markov and the Chainy Bunch

This is a project that I am doing to create board game themed words and phrases using a BoardGameGeek corpus. Project is built with python and a MariaDB database storing all the source data 

# Database Setup

The [database initialization scipt](/database/database.sql) will create the tables, views and stored procedures that I use to store and query boardgame data and various n-grams. The python database connections are leveraged using SQLAlchemy

# BoardGameGeek

Acquiring the board game data is just a matter of using Version 2 of the [BoardGameGeek XMLAPI](https://boardgamegeek.com/wiki/page/BGG_XML_API2). The script [get_games.py](get_games.py) basically loops through a series of potential game ids and records the id, title and description of positive results from the API. 

# N-Gram Generation

The other scripts are for generating and using ngrams for phrase generation. 
