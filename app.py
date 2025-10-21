import os
import telebot
from flask import Flask, request

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
APP_URL = "https://telegram-bot-x6zm.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("🚀 Starting Telegram Bot...")

# Автоматически устанавливаем веб-хук при запуске
try:
    bot.remove_webhook()
    webhook_url = f"{APP_URL}/webhook"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set: {webhook_url}")
except Exception as e:
    print(f"❌ Webhook error: {e}")

# Простые обработчики
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎉 Привет! Я работаю на Render! 🚀")

@bot.message_handler(commands=['test'])
def test_command(message):
    bot.reply_to(message, "✅ Бот активен!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Вы сказали: {message.text}")

# Веб-хук endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

# Статус страница
@app.route('/')
def status():
    return """
    <h1>🤖 Telegram Bot</h1>
    <p>✅ Бот запущен</p>
    <p>📱 URL: https://telegram-bot-x6zm.onrender.com</p>
    <p>🔗 Webhook: /webhook</p>
    <p>💡 Просто напиши боту /start</p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
