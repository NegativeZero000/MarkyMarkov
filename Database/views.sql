select
	(SELECT count(*) from game_detail) as 'Total known games',
	(SELECT count(*) from process where description_word_bigram = 1) as 'Descriptions processed for word bigrams',
	(SELECT count(*) from description_word_bigram) as 'Total word bigrams',
	(SELECT count(*) from process where title_letterpair_bigram = 1) as 'Titles processed for letter pair bigrams',
	(SELECT count(*) from title_letterpair_bigram) as 'Total letter pair bigrams'
from dual 
