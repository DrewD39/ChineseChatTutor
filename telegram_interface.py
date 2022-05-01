"""
Note that all Chinese 
"""
from conversation import Conversation
# import enum
import telebot
import os

token = os.environ["TELE_CHINESE_BOT_TOKEN"]


# bot.send_message('nh')


# class BotState(enum.IntEnum):
#     DEFAULT = 0
#     ADDING_ENGLISH = 1
#     ADDING_CHINESE = 2
#     REMOVING_ENGLISH = 3
#     REMOVING_CHINESE = 4
#     REVIEWING = 5

# Additional bot state.
class TelegramBot(telebot.TeleBot):
    # bot_state_machine = BotState.DEFAULT
    mod_card_english = ''
    mod_card_chinese = ''
    message_chat_id = None

    def __init__(self):
        super().__init__(token, parse_mode='markdown')
        self.conversation = Conversation(self.send_msg)

    def send_msg(self, text):
        self.send_message(
            chat_id=self.message_chat_id, text=text)

# @bot.message_handler(commands=['stop'])
# def stop(message):
#     bot.bot_state_machine = BotState.DEFAULT
#     # Reset state.
#     bot.mod_card_english = ''
#     bot.mod_card_chinese = ''
#     bot.send_message(chat_id=message.chat.id, text='Okay')

# @bot.message_handler(commands=['add'])
# def send_add(message):
#     if bot.bot_state_machine != BotState.DEFAULT:
#         bot.send_message(chat_id=message.chat.id, text='Cannot add a card right now')
#         return
#     bot.send_message(chat_id=message.chat.id, text=f'What is the English word/phrase to add?')
#     bot.bot_state_machine = BotState.ADDING_ENGLISH

bot = TelegramBot()

# Everything else.
@bot.message_handler()
def handle_standard_message(message):
    # # if bot.bot_state_machine == BotState.DEFAULT:
    # if bot.bot_state_machine == BotState.ADDING_ENGLISH:
    #     bot.mod_card_english = message.text
    #     bot.reply_to(message, text='and what is the translation in Chinese?')
    #     bot.bot_state_machine = BotState.ADDING_CHINESE
    # elif bot.bot_state_machine == BotState.ADDING_CHINESE:
    #     bot.mod_card_chinese = message.text
    #     card_set.add_card(bot.mod_card_english, bot.mod_card_chinese)
    #     bot.send_message(chat_id=message.chat.id, text=f'Card Added! ({bot.mod_card_english}, {bot.mod_card_chinese})')
    #     bot.bot_state_machine = BotState.DEFAULT
    bot.message_chat_id = message.chat.id
    bot.conversation.handle_message(message.text)

    # if bot.bot_state_machine == BotState.REMOVING_ENGLISH:
    # if bot.bot_state_machine == BotState.REMOVING_CHINESE:
    # if bot.bot_state_machine == BotState.REVIEWING:
    # bot.send_message(chat_id=message.chat.id, text="<a href='plecoapi://x-callback-url/s?q=晚安'>Pleco</a>")
    # bot.send_message(chat_id=message.chat.id, text="plecoapi://x-callback-url/s?q=晚安")


# Live on forever.
bot.infinity_polling()
