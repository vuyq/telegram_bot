import os
from flask import Flask, request
import telebot

BOT_TOKEN = "8442541152:AAFQX-qeG2vOYk-T4qyRGPHkYS92e7ufXv0"
APP_URL = "https://your-real-app-name.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот запущен!")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, f"Вы сказали: {message.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return 'ok', 200

@app.route('/')
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/webhook')
    return f'Webhook set for {APP_URL}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
