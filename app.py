import os
import requests
import urllib3
from flask import Flask, request
import telebot

# Отключаем предупреждения SSL (для тестирования)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')

# Автоматическое определение URL для Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    APP_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}"
else:
    # Временный URL - замени после деплоя на реальный
    APP_URL = "https://your-app-name.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print(f"🚀 Bot started!")
print(f"📱 APP_URL: {APP_URL}")
print(f"🔑 BOT_TOKEN exists: {bool(BOT_TOKEN)}")
print(f"🧠 GIGACHAT_API_KEY exists: {bool(GIGACHAT_API_KEY)}")

# Упрощенная версия GigaChat для тестирования
class SimpleGigaChat:
    def send_message(self, message_text):
        if not GIGACHAT_API_KEY:
            return "❌ GigaChat API ключ не настроен. Добавьте GIGACHAT_API_KEY в переменные окружения Render."
        
        try:
            # Простая заглушка - замени на реальный API вызов
            return f"🤖 GigaChat ответил бы на: '{message_text}'\n\n(Реальная интеграция требует настройки OAuth2 с GigaChat API)"
            
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

# Инициализация GigaChat
gigachat = SimpleGigaChat()

# Обработчики Telegram бота
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = f"""
🤖 Привет! Я тестовый бот с GigaChat.

📊 Статус:
• Бот активен: ✅
• GigaChat: {'✅' if GIGACHAT_API_KEY else '❌'}
• URL: {APP_URL}

Просто напиши мне любое сообщение!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['test'])
def test_command(message):
    """Тестовая команда для проверки работы"""
    bot.reply_to(message, "✅ Бот работает! GigaChat готов к работе.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех текстовых сообщений"""
    # Игнорируем команды
    if message.text.startswith('/'):
        return
    
    # Отправляем "печатает..." статус
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ от GigaChat
    response = gigachat.send_message(message.text)
    
    # Отправляем ответ
    bot.reply_to(message, response)

# Веб-хук для Render
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"Error processing update: {e}")
        return "Error", 500

@app.route("/")
def webhook():
    try:
        # Устанавливаем веб-хук
        bot.remove_webhook()
        webhook_url = f"{APP_URL}/{BOT_TOKEN}"
        success = bot.set_webhook(url=webhook_url)
        
        status_text = f"""
✅ Бот активен!
• Webhook: {webhook_url}
• GigaChat: {'✅ Настроен' if GIGACHAT_API_KEY else '❌ Не настроен'}
• SetWebhook: {'✅ Успешно' if success else '❌ Ошибка'}

Для настройки GigaChat:
1. Получи API ключ на developers.sber.ru
2. Добавь GIGACHAT_API_KEY в Environment Variables в Render
        """
        return status_text
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

@app.route("/test")
def test_page():
    """Страница для тестирования работы приложения"""
    return f"""
<h1>🤖 Telegram Bot Status</h1>
<p><strong>Status:</strong> ✅ Active</p>
<p><strong>URL:</strong> {APP_URL}</p>
<p><strong>Bot Token:</strong> {'✅ Set' if BOT_TOKEN else '❌ Missing'}</p>
<p><strong>GigaChat API:</strong> {'✅ Set' if GIGACHAT_API_KEY else '❌ Missing'}</p>
<hr>
<p>Теперь установи веб-хук в BotFather:</p>
<code>/setwebhook {APP_URL}/{BOT_TOKEN}</code>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
