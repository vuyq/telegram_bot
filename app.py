import os
import requests
import urllib3
from flask import Flask, request
import telebot
import json

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')
APP_URL = "https://telegram-bot-x6zm.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("🚀 Starting Telegram Bot with GigaChat...")
print(f"🔑 BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"🧠 GIGACHAT_API_KEY: {'✅' if GIGACHAT_API_KEY else '❌'}")

# Автоматически устанавливаем веб-хук при запуске
try:
    bot.remove_webhook()
    webhook_url = f"{APP_URL}/webhook"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set: {webhook_url}")
except Exception as e:
    print(f"❌ Webhook error: {e}")

# Упрощенная реализация GigaChat с диагностикой
class SimpleGigaChat:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        self.is_configured = bool(self.api_key)
    
    def send_message(self, message_text):
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_API_KEY в настройках Render."
        
        try:
            # Имитация работы GigaChat для теста
            # ЗАМЕНИ ЭТУ ЧАСТЬ НА РЕАЛЬНЫЙ API GIGACHAT КОГДА ПОЛУЧИШЬ КЛЮЧ
            response = f"""🤖 GigaChat Response (тестовый режим)

Ваш запрос: "{message_text}"

📊 Статус: GigaChat API ключ получен
🔑 Ключ: {self.api_key[:10]}...{self.api_key[-10:]}

💡 Для реальной работы с GigaChat:
1. Получи API ключ на developers.sber.ru
2. Замени этот код на реальный API вызов
3. Используй официальную документацию GigaChat

А пока я просто эхо-бот! 🎯"""
            
            return response
            
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

# Инициализация GigaChat
gigachat = SimpleGigaChat()

# Обработчики сообщений
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"""
🤖 Привет! Я бот с интеграцией GigaChat

📊 Статус системы:
• Бот: ✅ Активен
• GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
• Сервер: {APP_URL}

💡 Команды:
/start - это сообщение
/test - тест работы бота
/status - статус системы

Просто напиши мне любой вопрос!
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['test'])
def test_command(message):
    test_response = gigachat.send_message("Тестовое сообщение")
    bot.reply_to(message, test_response)

@bot.message_handler(commands=['status'])
def status_command(message):
    status_text = f"""
📊 Статус системы:

• Бот: ✅ Активен
• GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
• Webhook: {APP_URL}/webhook
• API Key: {'✅ Есть' if GIGACHAT_API_KEY else '❌ Нет'}

Для настройки GigaChat:
1. Получи API ключ на developers.sber.ru
2. Добавь GIGACHAT_API_KEY в Environment Variables в Render
3. Обнови код для реальных API вызовов
"""
    bot.reply_to(message, status_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Показываем что бот печатает
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ от GigaChat
    response = gigachat.send_message(message.text)
    
    # Отправляем ответ
    bot.reply_to(message, response)

# Веб-хук endpoint
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

# Статус страница
@app.route('/')
def status():
    webhook_info = bot.get_webhook_info()
    return f"""
    <h1>🤖 Telegram Bot + GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>URL:</strong> {APP_URL}</p>
    <p><strong>Webhook:</strong> {webhook_info.url}</p>
    <p><strong>GigaChat:</strong> {'✅ Configured' if gigachat.is_configured else '❌ Not configured'}</p>
    <hr>
    <h3>📝 Инструкция:</h3>
    <ol>
    <li>Напиши боту <code>/start</code> в Telegram</li>
    <li>Проверь работу <code>/test</code></li>
    <li>Для GigaChat получи API ключ на developers.sber.ru</li>
    </ol>
    """

@app.route('/debug')
def debug():
    """Страница отладки"""
    return {
        "bot_token_exists": bool(BOT_TOKEN),
        "gigachat_key_exists": bool(GIGACHAT_API_KEY),
        "app_url": APP_URL,
        "webhook_url": f"{APP_URL}/webhook"
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port)
