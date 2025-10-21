import os
import requests
import urllib3
from flask import Flask, request
import telebot

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')

# Автоматическое определение URL
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    APP_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}"
else:
    APP_URL = None  # Будем использовать позже

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("=" * 50)
print("🤖 BOT STARTED")
print(f"🔑 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🧠 GIGACHAT: {'✅' if GIGACHAT_API_KEY else '❌'}")
print(f"🌐 RENDER_HOSTNAME: {RENDER_EXTERNAL_HOSTNAME}")
print("=" * 50)

# Простой обработчик для теста
@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(f"📨 Received /start from {message.chat.id}")
    bot.reply_to(message, "🎉 Бот работает! Привет от Render!")

@bot.message_handler(commands=['test'])
def test_command(message):
    bot.reply_to(message, "✅ Тест пройден! Бот отвечает!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Эхо: {message.text}")

# Веб-хук
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return "Error", 500

# Главная страница для установки веб-хука
@app.route("/")
def index():
    if not APP_URL:
        return """
        <h1>❌ APP_URL не настроен</h1>
        <p>Добавьте в код ваш реальный URL из Render</p>
        <p>Текущий RENDER_EXTERNAL_HOSTNAME: {}</p>
        """.format(RENDER_EXTERNAL_HOSTNAME)
    
    try:
        # Пробуем установить веб-хук
        bot.remove_webhook()
        webhook_url = f"{APP_URL}/webhook"
        success = bot.set_webhook(url=webhook_url)
        
        return f"""
        <h1>🤖 Telegram Bot</h1>
        <p><strong>Status:</strong> ✅ Active</p>
        <p><strong>URL:</strong> {APP_URL}</p>
        <p><strong>Webhook:</strong> {webhook_url}</p>
        <p><strong>SetWebhook:</strong> {'✅ Success' if success else '❌ Failed'}</p>
        <hr>
        <h3>📝 Инструкция:</h3>
        <p>1. Установи веб-хук в BotFather:</p>
        <code>/setwebhook {webhook_url}</code>
        <p>2. Проверь бота командой /start</p>
        """
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Ручная установка веб-хука
@app.route("/set_webhook")
def set_webhook_manual():
    if not APP_URL:
        return "APP_URL не настроен"
    
    bot.remove_webhook()
    webhook_url = f"{APP_URL}/webhook"
    success = bot.set_webhook(url=webhook_url)
    
    return f"""
    Webhook установлен: {success}
    <br>URL: {webhook_url}
    <br><a href="/">Назад</a>
    """

@app.route("/get_webhook_info")
def get_webhook_info():
    """Проверка текущего веб-хука"""
    try:
        info = bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
