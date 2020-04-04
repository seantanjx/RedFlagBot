import telebot
import time as t
import datetime
import random
import urllib
import requests
import os
import json
import calendar
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from uuid import uuid4
from telegram.ext import updater, CommandHandler, MessageHandler, Filters
from firebase import firebase
from flask import Flask, request

TOKEN = 'Your token'
bot = telebot.TeleBot(token=TOKEN)
server = Flask(__name__)

firebase = firebase.FirebaseApplication(
    "DB_URL", None)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='heroku_URL' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

#hrome_options = webdriver.ChromeOptions()
#chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--no-sandbox")
#driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

name = 'RedFlaggerBot'
weatherlist = ['Summer', 'Spring', 'Autumn', 'Winter']
responses = {
    "name": [
        "my name is {0}".format(name),
        "they call me {0}".format(name),
        "I go by {0}".format(name)
    ],
    "weather": [
        "the weather is {0}".format(random.choice(weatherlist)),
        "it's {0} today".format(random.choice(weatherlist))
    ],
    "creator": [
        "I'm created by YingTing, Sean and Timothy."
    ], "born": [
        "I'm born on 18 January 2020, a capricorn baby just like Stephen Hawking!",
        "I'm born on 18 January 2020, born on a small planet called pluto",
        "I'm born on 18 January 2020, a loving kindness bot who aspires to love.",
        "A master of none but the cutest giant bot born on 18 January 2020."
    ], "feeling": [
        "I'm feeling pretty lonely, but with you talking to me it brightens my day",
        "I'm feeling extremely happy, I have you around to be able to talk to me",
        "I'm feeling extremely joyous today, I' have someone that is willing to talk to me!",
        "I'm feeling sad, after my creator created me, he left me alone to my own demise."
    ],
    "default": ["default message"]
}

new_list = []
with open("negative-words.txt", "r") as f:
    for line in f:
        new_list.append(line.rstrip("\n"))


def get_tweets(twitter_username, orig_rating):
    driver = webdriver.Chrome()
    url = "https://twitter.com/" + twitter_username.lower()
    driver.get(url)

    tweet_index = 0
    counter = 0
    dt = {}

    SCROLL_PAUSE_TIME = 1
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    while tweet_index <= 50:
        tweet = driver.find_elements_by_xpath(
            '//p[@class = "TweetTextSize TweetTextSize--normal js-tweet-text tweet-text"]')
        time = driver.find_elements_by_xpath(
            '//span[contains(@class,"_timestamp")]')
        length = len(tweet)
        for i in range(length):
            dt[i + 1 + counter * 20] = [tweet[i].text, time[i].text]
        tweet_index += length
        counter += 1

        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        t.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.close()
    rating = check_rating(dt)
    last_check_date = datetime.date.today()
    return [orig_rating - rating, last_check_date]


def check_rating(dt):
    counter = 0
    for value in dt.values():
        wordsplit = value[0].split(" ")
        for word in wordsplit:
            if word in new_list:
                counter += 0.1
    return counter


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Im a RedFlagBot created by TeamRedFlag, born on 18 Jan 2020. I am here to show concern and love for all of you, to begin please type /discretion or /begin or /information to know more about me.')


@bot.message_handler(commands=['begin'])
def send_begin(message):
    bot.reply_to(message, "Please type your twitter name WITH @ INFRONT")


@bot.message_handler(commands=['discretion'])
def send_discretion(message):
    bot.reply_to(message, "Upon keying in your child's twitter user handle, you consent to the bot in reading and interpreting your child's social information.")


@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message, "这个机器是嫈婷，嘉轩和智慧创建的！👻")


def findTwitterName(msg):
    for word in msg:
        if '@' in word:
            return word


def validateMessages(msg):
    for word in msg:
        if '@' not in word:
            return word


@bot.message_handler(func=lambda msg: msg.text is not None and '@' not in msg.text)
def random_responses(message):
    texts = message.text.split()
    for word in texts:
        if word not in responses:
            pass
        else:
            random_talk = random.choice(responses[word])
            bot.reply_to(message, random_talk)


@bot.message_handler(func=lambda msg: msg.text is not None and '@' in msg.text)
def twitterConverter(message):
    texts = message.text.split()
    find_texts = findTwitterName(texts)
    if find_texts == '@':
        pass
    else:
        twitter_link = 'https://twitter.com/{}'.format(find_texts[1:])
        if twitter_link == None:
            bot.reply_to(
                message, 'Please retype your child\'s twitter username as it is invalid')

        bot.reply_to(message, twitter_link)
        check_user = firebase.get(
            "/telechatdetails", message.chat.id, connection=None)
        if check_user == None:
            store = get_tweets(find_texts[1:], 5)
        else:
            rate = 0
            twitName = ""
            data_rating = firebase.get(
                "/telechatdetails/"+str(message.chat.id), "", connection=None)
            for key, value in data_rating.items():
                if key == "rating":
                    rate = value
                elif key == "twitterName":
                    twitName = value
            store = get_tweets(twitName, rate)

        if round(store[0], 1) < 2.0 and round(store[0], 1) > 0:
            bot.reply_to(message, "WARNING! Pay more attention to your child!")
            bot.reply_to(message, "Your child's rating is " +
                         str(round(store[0], 1)) + " as of " + str(store[1]))
        elif round(store[0], 1) <= 0:
            store[0] = 5
            bot.reply_to(
                message, "CRITICAL! Your child needs more care and concern!")
        else:
            bot.reply_to(message, "Your child's rating is " +
                         str(round(store[0], 1)) + " as of " + str(store[1]))

        data = {
            'chatID': message.chat.id,
            'twitterName': find_texts[1:],
            'rating': round(store[0], 1)
        }
        result = firebase.put("/telechatdetails",
                              message.chat.id, data, connection=None)


while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)
