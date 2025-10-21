import os
from flask import Flask, request
import telebot

# Получаем токен из переменных окружения (их мы позже зададим на Render)
BOT_TOKEN = '8442541152:AAFQX-qeG2vOYk-T4qyRGPHkYS92e7ufXv0'
# Ссылка на ваше приложение на Render (будет позже)
APP_URL = f"https://your-app-name.onrender.com"

# Создаем экземпляр бота и веб-приложения Flask
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я эхо-бот. Просто напиши мне что-нибудь.")

# Обработчик всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# Веб-хук для Render. Этот маршрут вызывается Telegram для пересылки сообщений.
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# Маршрут для установки веб-хука
@app.route("/")
def webhook():
    # Удаляем старый веб-хук, ставим новый на наш URL на Render
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/' + BOT_TOKEN)
    return "Бот активен!", 200

# Этот блок кода нужен для запуска на Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
