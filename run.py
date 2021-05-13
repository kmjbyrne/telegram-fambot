import re
import sys
import logging

from threading import Thread
from datetime import datetime
from random import randrange

import requests
import yaml

from pydantic import BaseModel
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import Updater
from telegram import Bot
from telegram.ext.filters import Filters


logger = logging.getLogger(__name__)


class Config(BaseModel):
    token: str
    group: str


config: Config
with open('config.yaml') as file:
    contents = yaml.load(file, Loader=yaml.FullLoader)
    config = Config(**contents)


updater = Updater(token=config.token, use_context=True)
bot = Bot(token=config.token)


if len(sys.argv) > 1 and sys.argv[1] == 'send':
    def do():
        Bot(token=config.token).send_message(chat_id=config.group, text=sys.argv[2])
    Thread(target=do).start()


def news():
    now = datetime.now()
    this_day = requests.get(f'http://numbersapi.com/{now.month}/{now.day}/date').text
    fact = requests.get('https://uselessfacts.jsph.pl/random.json?language=en').json().get('text')
    message = (
        "Good morning family!"
        "Hope all is well and all the best in your exams/study today Rósín :)"
    )
    meme = requests.get('https://meme-api.herokuapp.com/gimme').json().get('url')
    bot.send_message(chat_id=config.group, text=message)
    bot.send_message(chat_id=config.group, text=f"On this day {now.strftime('%Y-%m-%d')}")
    bot.send_message(chat_id=config.group, text=this_day)
    bot.send_message(chat_id=config.group, text=fact)
    bot.send_photo(chat_id=config.group, photo=meme)


scheduler = BackgroundScheduler()
scheduler.add_job(news, CronTrigger.from_crontab('0 12 * * *'))
scheduler.start()

data = requests.get("https://api.telegram.org/bot{config.token}/getUpdates")


def help(update, context):
    emoji = b'\xF0\x9F\x98\x8D'
    message = (
        "Available bot commands\n"
        f"{str(emoji.decode())}\n"
        "/love get some love from the bot\n"
        "/fact Generates a random fact from the random fact API\n"
        "/wifi WiFi password\n"
        "/meme Web crawl sub Reddits for a meme\n"
        "/hype Hype up for GemFest2021\n"
        "/help Help\n\n"
        "/auto daily facts, afternoon meme and 'today in the past' fact\n"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='MarkdownV2')


def hype(update, context):
    selector = randrange(4)
    hypes = [
        "Big party hype woot woot!",
        "Gemma is so amazing and her party will be amazing woot!",
        "BBQ cocktails and big fun yeah boi!",
        "Niall gonna get some Mc lovin' howaya now",
        "Rupali gonna think we are absolute loonies :) :)" +
        str(b'\xF0\x9F\x98\x82')
    ]

    context.bot.send_message(chat_id=update.effective_chat.id, text=hypes[selector])


def meme(update, context):
    meme = requests.get('https://meme-api.herokuapp.com/gimme').json().get('url')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=meme)


def love(update, context):
    user = update.effective_user.full_name
    print(update)
    message = f'Awww, love you too, {user}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def fact(update, context):
    fact = requests.get('https://uselessfacts.jsph.pl/random.json?language=en').json().get('text')
    context.bot.send_message(chat_id=update.effective_chat.id, text=fact)


def wifi(update, context):
    user = update.effective_user.full_name
    message = f"Hey {user}, the wifi password is: 07001607"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def all_message_callback(update, context):
    from datetime import datetime

    now = datetime.now()
    days = datetime(2021, 5, 23) - now
    title = f'BBQ Bitches ({days.days} days ETA)'

    context.bot.set_chat_title(update.effective_chat.id, title)


def message_callback(update, context):
    user = update.effective_user.full_name
    message = f"Hey {user}, stop that now."
    # context.bot.edit_message_text('test', chat_id=update.effective_chat.id,
    #                               message_id=update.effective_message.message_id)
    original: str = update.effective_message.text

    replace = re.sub(r'(?i)(COVID|pandemic|corona|covid)', 'rainbows and unicorns', original)
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.bot.send_message(chat_id=update.effective_chat.id, text=replace)


def gemma_callback(update, context):
    message = f"THE BIRTHDAY GIRL WHOS PARTY IT IS NEXT WEEK YEEESSSSSSSS"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def add_todo(update, context):
    path = 'store.yaml'
    with open(path, 'r+') as file:
        contents = yaml.load(file)

        STORE = contents

        todo = ''.join(update.effective_message.text.split('/todo ')[1:])
        if STORE.get(update.effective_user.first_name, None):
            STORE[update.effective_user.first_name].append(todo)
        else:
            STORE[update.effective_user.first_name] = []
            STORE[update.effective_user.first_name].append(todo)

    with open(path, 'w') as file:
        file.write(yaml.dump(STORE))


def done(update, context):
    path = 'store.yaml'
    with open(path, 'r+') as file:
        contents = yaml.load(file)

        todo = ''.join(update.effective_message.text.split('/done ')[1:])

        STORE = contents
        values: list = STORE[update.effective_user.first_name]
        values.pop(int(todo))

    with open(path, 'w') as file:
        file.write(yaml.dump(STORE))


def list_todos(update, context):
    with open('store.yaml', 'r') as file:
        contents = yaml.load(file)

    STORE = contents

    message = ""
    for (key, value) in STORE.items():
        message += f"\n\n{key} Todos:\n"

        task: str
        for idx, task in enumerate([i for i in value if len(i)]):
            message += f"\n{idx}: {task.title()}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


covid_regex = r'(?i)(COVID|pandemic|corona|covid)'
message_handler = MessageHandler(Filters.regex(covid_regex) & (~Filters.command), message_callback)
all_messages = MessageHandler(Filters.all & (~Filters.command), all_message_callback)
gemma_handler = MessageHandler(Filters.regex(r'(Gemma)') & (~Filters.command), gemma_callback)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('hype', hype))
dispatcher.add_handler(CommandHandler('love', love))
dispatcher.add_handler(CommandHandler('fact', fact))
dispatcher.add_handler(CommandHandler('wifi', wifi))
dispatcher.add_handler(CommandHandler('meme', meme))
dispatcher.add_handler(CommandHandler('todo', add_todo))
dispatcher.add_handler(CommandHandler('todos', list_todos))
dispatcher.add_handler(CommandHandler('done', done))
dispatcher.add_handler(message_handler)
dispatcher.add_handler(gemma_handler)
dispatcher.add_handler(all_messages)


if __name__ == '__main__':
    try:
        updater.start_polling()
    except KeyboardInterrupt:
        updater.stop()
        scheduler.shutdown()
