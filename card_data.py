import enum
import logging
import math
import operator
import os
import pickle
import random
import time

# What factor to increase the review interval by upon success/failure.
study_interval_modifier = 1.5

# Link to website for breakdown of traditional characters. 
LOOKUP_URL = 'https://www.moedict.tw/'

# Default cards to put in all decks. Includes most bot commands.
DEFAULT_CARDS = [('add','添加'),
                ('remove','消除'),
                ('website','網址'),
                ('help','幫助'),
                ('practice','實踐'),
                ('summary','概括'),
                ('list','列表'),
                ('english language','英文'),
                ('chinese language','中文'),
               ]

# Parent directory of this file.
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE_PATH = os.path.join(PARENT_DIR, '.cards.pkl')

logging.basicConfig(level=logging.INFO)


class CardSelection(enum.IntEnum):
    RANDOM = 0
    CONFIDENCE_WEIGHTED = 1
    STRICT_ORDERED = 2
    RANDOM_READY = 3

class Card:
    """A card represents a single word/phrase to be studied."""
    english = ''
    chinese = ''
    num_attempts = 0
    num_successes = 0
    last_attempt = 0
    study_interval = 1  # days
    confidence_index = 0

    def __init__(self, english, chinese):
        self.english = english.lower().strip()
        self.chinese = chinese.strip()

    def to_string(self):
        """Return a string representation of the card."""
        return f'{self.english}\n{self.chinese}\nSuccesses: {self.num_successes}\n'\
               f'Attempts: {self.num_attempts}\nLast Attempt: {self.last_attempt}\n'\
               f'Study Interval: {self.study_interval}\nConfidence: {self.confidence_index}'

    def get_link(self):
        """Return a string containing a link to the chinese characters information."""
        # return 'plecoapi://x-callback-url/s?q=' + self.chinese # Universal Pleco link
        return LOOKUP_URL + self.chinese

    def review_result(self, success):
        """Update the card based on the result of review."""
        self.last_attempt = time.time()
        self.num_attempts += 1
        if success:
            self.num_successes += 1
            self.study_interval = math.ceil(
                self.study_interval * study_interval_modifier)
            self.confidence_index = min(1, self.confidence_index + (0.1 * (self.num_successes / self.num_attempts)))
        else:
            self.study_interval = max(
                1, self.study_interval // study_interval_modifier)
            self.confidence_index = max(0, self.confidence_index - 0.1)


class CardDeck:
    num_attempts = 0
    num_successes = 0

    def __init__(self):
        try:
            with open(DATA_FILE_PATH, "rb") as file_in:
                self.cards = pickle.load(file_in)
        except FileNotFoundError:
            logging.warning('No cards file detected. Creating an empty card set.')
            self.cards = []
            for pair in DEFAULT_CARDS:
                self.cards.append(Card(pair[0], pair[1]))
        self.refresh()

    def refresh(self):
        """Update totals, sort cards based on confidence index, save to disk."""
        # Update success/failure counts.
        num_successes = 0
        num_attempts = 0
        for card in self.cards:
            num_successes += card.num_successes
            num_attempts += card.num_attempts
        self.num_successes = num_successes
        self.num_attempts = num_attempts

        # Sort by least -> most confidence.
        self.cards.sort(key=operator.attrgetter('confidence_index'))

        # Save to disk.
        with open(DATA_FILE_PATH, 'wb') as out_file:
            pickle.dump(self.cards, out_file, pickle.HIGHEST_PROTOCOL)

    def add_card(self, english, chinese):
        # Ignore duplicates, where both English and Chinese match.
        if any([english == existing_card.english and chinese == existing_card.chinese for existing_card in self.cards]):
            logging.warning(f'Ignoring duplicate card: {english}, {chinese}')
            return False
        card = Card(english, chinese)
        self.cards.append(card)
        self.refresh()
        return True

    def remove_card(self, english_or_chinese):
        for i in range(len(self.cards)):
            if self.cards[i].english == english_or_chinese or self.cards[i].chinese == english_or_chinese:
                self.cards.pop(i)
                self.refresh()
                return True
        logging.warning(f'Card was not found, no removal performed')
        return False

    def summary(self):
        """Return string summarizing the state of the user CardDeck."""
        self.refresh()
        if len(self.cards) == 0:
            return "There are no cards in the deck. Use 'add' to add some!"
        return_str = ''
        return_str += f'This study set contains {len(self.cards)} cards.'
        return_str += f'\n{self.num_attempts} cards have been reviewed ({(self.num_successes / max(1, self.num_attempts) * 100):.2f}% success rate).'
        return_str += f'\nThe average confidence index is {sum([card.confidence_index for card in self.cards])/len(self.cards):.2f}'
        return return_str

    def list_all(self):
        """Return a string containing all cards (english, chinese)."""
        self.refresh()
        if len(self.cards) == 0:
            return "There are no cards in the deck. Use 'add' to add some!"
        ret_string = ''
        for card in self.cards:
            ret_string += f'{card.english}, {card.chinese}  ({card.confidence_index:.2f})\n'
        return ret_string.rstrip()

    def select_card(self, method=CardSelection.RANDOM):
        """Select a card at random with preference given to the least well known cards."""
        """Select any card that is ready to be reviewed."""
        # Refresh to update confidence changes. Super innefficient.
        self.refresh()
        if method == CardSelection.RANDOM:
            return self.cards[random.randint(0, len(self.cards)-1)]
        # Very basic algorithm to give preference weight to low indices.
        # Note that 0 idx does not get as much weight as it should, but it is enough.
        elif method == CardSelection.CONFIDENCE_WEIGHTED:
            index = abs(random.randint(0, len(self.cards)-1) - random.randint(0, len(self.cards)-1))
            return self.cards[index]


# FOR TESTING.
if __name__ == "__main__":
    card_set = CardDeck()
    card = Card('hello', '你好')
    card_set.add_card(card)
    logging.info(card_set)
    # logging.info([existing_card.to_string() for existing_card in card_set.cards])
    logging.info(card_set.select_card().to_string())
    # card_set.remove_card('hello', '你好')
    logging.info([existing_card.to_string() for existing_card in card_set.cards])

