# This file manages the state machine of the conversation so that a user can intereact with
# the card data seamlessly.
from card_data import CardDeck, CardSelection, LOOKUP_URL
import enum
import logging


logging.basicConfig(level=logging.INFO)


CMD_PREFIX = '/'

CMD_STOP = 'stop'
CMD_ADD = '添加'
CMD_REMOVE = '消除'
CMD_LINK = '網址'
CMD_HELP = '幫助'
CMD_REVIEW = '實踐'
CMD_SUMMARY = '概括'
CMD_ALL = '列表'
CMD_REVIEW_ENG = '英文'
CMD_REVIEW_CHI = '中文'
CMDS = [CMD_STOP, CMD_ADD, CMD_REMOVE, CMD_LINK, CMD_SUMMARY, CMD_ALL, CMD_REVIEW, CMD_REVIEW_ENG, CMD_REVIEW_CHI, CMD_HELP]

REVIEW_CMD_LINK = '網址'
REVIEW_CMD_CHINESE = '中文'
REVIEW_CMD_ENGLISH = '英文'
REVIEW_CMD_PASS = '知道'
REVIEW_CMD_FAIL = '不知道'
REVIEW_CMDS = [REVIEW_CMD_LINK, REVIEW_CMD_CHINESE, REVIEW_CMD_ENGLISH, REVIEW_CMD_FAIL, REVIEW_CMD_PASS]


class BotState(enum.IntEnum):
    IDLE = 0
    ADDING_ENGLISH = 1
    ADDING_CHINESE = 2
    REMOVING = 3
    #  = 4
    REVIEWING_ENG = 5
    REVIEWING_CHI = 6

class Conversation():
    """


    Note that all state flows are sequential, except for the stop command, which returns to default
    idle state.
    """
    editing_card_english = ''
    editing_card_chinese = ''
    reviewing_card = None

    def __init__(self, message_function):
        self.card_deck = CardDeck()
        self.message_function = message_function
        self.state = BotState.IDLE
    
    def set_state(self, state):
        """Set the state machine to state and execute logic for the state."""
        self.state = state
        if state == BotState.IDLE:
            self.message_function(f"oke. let me know if you need '{CMD_HELP}'")
        elif state == BotState.ADDING_ENGLISH:
            self.editing_card_english = ''
            self.editing_card_chinese = ''
            self.message_function("What is an English word/phrase to add?\n(Send 'stop' to finish adding words)")
        elif state == BotState.ADDING_CHINESE:
            self.message_function('and what is the Chinese translation?')
        elif state == BotState.REMOVING:
            self.editing_card_english = ''
            self.editing_card_chinese = ''
            self.message_function("What is the English or Chinese word/phrase to remove?\(Send 'stop' to finish removing words)")
        elif state == BotState.REVIEWING_ENG:
            self.message_function("Beginning a review session of eng->chi\nglhf\n(Send 'stop' when you're done)")
            self.new_card_and_message()
        elif state == BotState.REVIEWING_CHI:
            self.message_function("Beginning a review session of chi->eng\nglhf\n(Send 'stop' when you're done)")
            self.new_card_and_message()
        else:
            logging.error(f'No logic implemented for entering the {state} state!')

    def new_card_and_message(self):
        self.reviewing_card = self.card_deck.select_card(CardSelection.CONFIDENCE_WEIGHTED)
        if self.state == BotState.REVIEWING_ENG:
            self.message_function(self.reviewing_card.english)
        elif self.state == BotState.REVIEWING_CHI:
            self.message_function(self.reviewing_card.chinese)
        else:
            logging.error(f'Non-supported card selection state: {self.state}')

    def handle_message(self, text):
        text = text.strip().lower()
        # If text is empty or whitespace only.
        if not text:
            return
        # All states can return to IDLE with stop command.
        if text == CMD_STOP:
            self.set_state(BotState.IDLE)
            return

        # Handle commands from the idle state.
        if self.state == BotState.IDLE:
            cmd = text.split()[0]
            if cmd == CMD_HELP:
                self.message_function(f'You can say any of these: {CMDS}')
            elif cmd == CMD_LINK:
                self.message_function(LOOKUP_URL + text[len(CMD_LINK)+1:])
            elif cmd == CMD_SUMMARY:
                self.message_function(self.card_deck.summary())
            elif cmd == CMD_ALL:
                list_strs = self.card_deck.list_all().split('\n')
                i = 0
                lines_per_msg = 200
                while i < len(list_strs):
                    self.message_function('\n'.join(list_strs[i:min(len(list_strs), i + lines_per_msg)]))
                    i += lines_per_msg
            elif cmd == CMD_ADD:
                self.set_state(BotState.ADDING_ENGLISH)

            elif cmd == CMD_REMOVE:
                if len(self.card_deck.cards) == 0: return
                self.set_state(BotState.REMOVING)

            elif cmd == CMD_REVIEW or cmd == CMD_REVIEW_ENG:
                if len(self.card_deck.cards) == 0: return
                self.set_state(BotState.REVIEWING_ENG)

            elif cmd == CMD_REVIEW_CHI:
                if len(self.card_deck.cards) == 0: return
                self.set_state(BotState.REVIEWING_CHI)
            else:
                self.message_function(f"I can't interpret that, but you can ask for '{CMD_HELP}'")

        # non-idle state commands
        elif self.state == BotState.ADDING_ENGLISH:
            self.editing_card_english = text
            self.set_state(BotState.ADDING_CHINESE)
        elif self.state == BotState.ADDING_CHINESE:
            self.editing_card_chinese = text
            if self.card_deck.add_card(self.editing_card_english, self.editing_card_chinese):
                self.message_function(f'Card added! ({self.editing_card_english}, {self.editing_card_chinese})')
            else:
                self.message_function(f'Card already exists, duplicate not added')
            self.set_state(BotState.ADDING_ENGLISH)
        

        elif self.state == BotState.REMOVING:
            if self.card_deck.remove_card(text):
                self.message_function(f'Card Removed! ({text})')
            else:
                self.message_function(f'Card not found and not removed')
            self.set_state(BotState.REMOVING)

        elif self.state == BotState.REVIEWING_ENG or self.state == BotState.REVIEWING_CHI:
            # Success!
            if ((self.state == BotState.REVIEWING_ENG and text == self.reviewing_card.chinese) or
                (self.state == BotState.REVIEWING_CHI and text == self.reviewing_card.english) or
                text == REVIEW_CMD_PASS):
                self.message_function(':)')
                self.reviewing_card.review_result(True)
                self.new_card_and_message()
            # Give up on the word.
            elif text == REVIEW_CMD_FAIL:
                self.message_function(':(')
                self.reviewing_card.review_result(False)
                self.new_card_and_message()
            # Request link to more info.
            elif text == REVIEW_CMD_LINK:
                self.message_function(self.reviewing_card.get_link())
            # Request to see the Chinese characters.
            elif text == REVIEW_CMD_CHINESE:
                self.message_function(self.reviewing_card.chinese)
            # Request to see the English words.
            elif text == REVIEW_CMD_ENGLISH:
                self.message_function(self.reviewing_card.english)
            # Incorrect guess.
            else:
                self.message_function(f"that's not it, try again!\nYou can also respond with {REVIEW_CMDS}")
                self.reviewing_card.review_result(False)
