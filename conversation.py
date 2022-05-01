# This file manages the state machine of the conversation so that a user can intereact with
# the card data seamlessly.
from card_data import CardDeck
import enum
import logging


logging.basicConfig(level=logging.INFO)


CMD_PREFIX = '/'

CMD_STOP = 'stop'
CMD_ADD = 'add'
CMD_REMOVE = 'remove'
CMD_HELP = 'help'
CMD_REVIEW = 'review'
CMD_SUMMARY = 'summary'
CMD_ALL = 'list'
CMD_REVIEW_ENG = 'english'
CMD_REVIEW_CHI = 'chinese'
CMDS = [CMD_STOP, CMD_ADD, CMD_REMOVE, CMD_HELP, CMD_SUMMARY, CMD_ALL, CMD_REVIEW, CMD_REVIEW_ENG, CMD_REVIEW_CHI]

REVIEW_CMD_LINK = 'more'
REVIEW_CMD_CHINESE = 'chinese'
REVIEW_CMD_ENGLISH = 'english'
REVIEW_CMD_PASS = 'yaa'
REVIEW_CMD_FAIL = 'idk'
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
        self.state = BotState.IDLE
        self.message_function = message_function
    
    def state_check_and_step(self, state_check, next_state=None):
        """Check if current state, if yes return True and iterate to given next step."""
        if self.state == state_check:
            if next_state is not None:
                self.state = next_state
            return True
        return False

    def new_card_and_message(self):
        self.reviewing_card = self.card_deck.select_card()
        if self.state == BotState.REVIEWING_ENG:
            self.message_function(self.reviewing_card.english)
        elif self.state == BotState.REVIEWING_CHI:
            self.message_function(self.reviewing_card.chinese)

    def handle_message(self, text):
        text = text.strip().lower()
        # If text is empty or whitespace only.
        if not text:
            return
        # All states can return to IDLE with stop command.
        if text == CMD_STOP:
            self.state = BotState.IDLE
            self.message_function('oke')
            return

        # Handle a command from the idle state.
        if text == CMD_HELP and self.state_check_and_step(BotState.IDLE):
            self.message_function(f'You can say any of these: {CMDS}')

        elif text == CMD_SUMMARY and self.state_check_and_step(BotState.IDLE):
            self.message_function(self.card_deck.summary())

        elif text == CMD_ALL and self.state_check_and_step(BotState.IDLE):
            list_strs = self.card_deck.list_all().split('\n')
            i = 0
            lines_per_msg = 200
            while i < len(list_strs):
                self.message_function('\n'.join(list_strs[i:min(len(list_strs) - 1, i + lines_per_msg)]))
                i += lines_per_msg

        elif text == CMD_ADD and self.state_check_and_step(BotState.IDLE, BotState.ADDING_ENGLISH):
            self.editing_card_english = ''
            self.editing_card_chinese = ''
            self.message_function('What is the English word/phrase?')

        elif text == CMD_REMOVE and self.state_check_and_step(BotState.IDLE, BotState.REMOVING):
            self.editing_card_english = ''
            self.editing_card_chinese = ''
            self.message_function('What is the English or Chinese word/phrase to remove?')

        elif (text == CMD_REVIEW or text == CMD_REVIEW_ENG) and self.state_check_and_step(BotState.IDLE, BotState.REVIEWING_ENG):
            self.message_function('Beginning a review session of eng->chi\nglhf')
            self.new_card_and_message()

        elif text == CMD_REVIEW_CHI and self.state_check_and_step(BotState.IDLE, BotState.REVIEWING_CHI):
            self.message_function('Beginning a review session of chi->eng\nglhf')
            self.new_card_and_message()

        elif self.state_check_and_step(BotState.IDLE):
            self.message_function(f"idk what you want.. but you can ask for 'help'")

        # non-idle state commands
        elif self.state_check_and_step(BotState.ADDING_ENGLISH, BotState.ADDING_CHINESE):
            self.editing_card_english = text
            self.message_function('and what is the Chinese translation?')

        elif self.state_check_and_step(BotState.ADDING_CHINESE, BotState.IDLE):
            self.editing_card_chinese = text
            if self.card_deck.add_card(self.editing_card_english, self.editing_card_chinese):
                self.message_function(f'Card added! ({self.editing_card_english}, {self.editing_card_chinese})')
            else:
                self.message_function(f'Card already exists, duplicate not added')

        elif self.state_check_and_step(BotState.REMOVING, BotState.IDLE):
            if self.card_deck.remove_card(text):
                self.message_function(f'Card Removed! ({text})')
            else:
                self.message_function(f'Card not found and not removed')

        elif self.state_check_and_step(BotState.REVIEWING_ENG) or self.state_check_and_step(BotState.REVIEWING_CHI):
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
