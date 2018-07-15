#!/usr/bin/env python3

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from ydict import YDict
from decision_maker import DecisionMaker
from wiki_spider import WikiSpider

import os 
# 维基百科爬虫
wiki = WikiSpider()

# 字典
yd = YDict()

# 决策者
deci = DecisionMaker()

def bot_setup():
    token = os.getenv('TGBOT_TOKEN')
    updater = Updater(token=token,  request_kwargs=wiki.request_kwargs)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    start_handler = CommandHandler('start', start)
    wiki_handler = MessageHandler(Filters.text, search_wiki_text)
    wiki_cmd_handler = CommandHandler('wiki', search_wiki_cmd, pass_args=True, allow_edited=True)
    decision_cmd_handler = CommandHandler('decide', decision_cmd, pass_args=True, allow_edited=True)
    dict_cmd_handler = CommandHandler('dict', dict_cmd, pass_args=True, allow_edited=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(wiki_handler)
    dispatcher.add_handler(wiki_cmd_handler)
    dispatcher.add_handler(decision_cmd_handler)
    dispatcher.add_handler(dict_cmd_handler)
    
    print('Bot started...')
    updater.start_polling()
    updater.idle()

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='wikiboy here!')

def search_wiki_text(bot, update):

    args = update.message.text.split(' ')
    search_wiki_cmd(bot, update, args)

def search_wiki_cmd(bot, update, args):

    if update['edited_message'] is not None:
        chat_id = update.edited_message.chat.id
    else:
        chat_id = update.message.chat_id
    # print(chat_id)

    kw = '%20'.join(args)
    print('接收关键词: {}'.format(kw))
    brief = wiki.tg_wiki(chat_id, kw)
    bot.send_message(chat_id=chat_id, text=brief)

def decision_cmd(bot, update, args):
    try:
        if update['edited_message'] is not None:
            chat_id = update.edited_message.chat.id
        else:
            chat_id = update.message.chat_id
        bot.send_message(chat_id=chat_id, text=deci.decide(args))
    except Exception as e:
        print(e)

def dict_cmd(bot, update, args):
    if update['edited_message'] is not None:
        chat_id = update.edited_message.chat.id
    else:
        chat_id = update.message.chat_id
    # print(chat_id)

    kw = '%20'.join(args)
    print('接收关键词: {}'.format(kw))
    bot.send_message(chat_id=chat_id, text=yd.query(kw))

def main():
    bot_setup()


if __name__ == '__main__':
    main()
