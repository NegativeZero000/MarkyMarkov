from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
class BoardGame(Base):
    __tablename__ = 'game_detail'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    process = relationship('Process', uselist=False, back_populates='game_detail')

    def __repr__(self):
        return "<BoardGame(id='{}', name='{}', description='{}'>".format(
            self.id, self.name, self.description
        )

class Process(Base):
    __tablename__ = 'process'
    game_id = Column(Integer, ForeignKey('game_detail.id'), primary_key=True)
    description_word_bigram = Column(Integer, nullable=True, default=0)
    title_letterpair_bigram = Column(Integer, nullable=True, default=0)
    game_detail = relationship('BoardGame', back_populates='process')

    def __repr__(self):
        return "<Process(game_id='{}', description_word_bigram='{}', title_letter_pair='{}''>".format(
            self.game_id, self.description_word_bigram, self.title_letter_pair
        )

class DescriptionWordBigram(Base):
    __tablename__ = 'description_word_bigram'
    first = Column(String(125), primary_key=True)
    second = Column(String(125), primary_key=True)
    frequency = Column(Integer)

    def add_frequency(self, count):
        self.frequency = self.frequency + count

    def __repr__(self):
        return "<DescriptionBigram(first='{}', second='{}', frequency='{}'>".format(
            self.first, self.second, self.frequency
        )

class TitleLetterPairBigram(Base):
    __tablename__ = 'title_letterpair_bigram'
    first = Column(String(2), primary_key=True)
    second = Column(String(2), primary_key=True)
    frequency = Column(Integer)

    def add_frequency(self, count):
        self.frequency = self.frequency + count

    def __repr__(self):
        return "<LetterPairBigram(first='{}', second='{}', frequency='{}'>".format(
            self.first, self.second, self.frequency
        )
