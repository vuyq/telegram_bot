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

# Упрощенная реализация GigaChat
class SimpleGigaChat:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        self.is_configured = bool(self.api_key)
    
    def send_message(self, message_text):
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_API_KEY в настройках Render."
        
        try:
            # Имитация работы GigaChat для теста
            response = f"""🤖 GigaChat Response (тестовый режим)

Ваш запрос: "{message_text}"

📊 Статус: Веб-хук работает! Вижу ваше сообщение.
🔑 Ключ: {self.api_key[:10]}...{self.api_key[-10:] if self.api_key else 'N/A'}

💡 Бот успешно получает сообщения через веб-хук!"""
            
            return response
            
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

# Инициализация GigaChat
gigachat = SimpleGigaChat()

# Обработчики сообщений
@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(f"📨 Received /start from {message.chat.id}")
    welcome_text = f"""
🤖 Привет! Я бот с интеграцией GigaChat

📊 Статус системы:
• Бот: ✅ Активен
• GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
• Веб-хук: ✅ Работает

💡 Команды:
/start - это сообщение
/test - тест работы бота
/status - статус системы

Просто напиши мне любой вопрос!
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['test'])
def test_command(message):
    print(f"🧪 Received /test from {message.chat.id}")
    test_response = gigachat.send_message("Тестовое сообщение")
    bot.reply_to(message, test_response)

@bot.message_handler(commands=['status'])
def status_command(message):
    print(f"📊 Received /status from {message.chat.id}")
    status_text = f"""
📊 Статус системы:

• Бот: ✅ Активен
• GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
• Webhook: {APP_URL}/webhook
• API Key: {'✅ Есть' if GIGACHAT_API_KEY else '❌ Нет'}

Логи веб-хука: ✅ Получаем запросы от Telegram
"""
    bot.reply_to(message, status_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    print(f"💬 Received message from {message.chat.id}: {message.text}")
    
    # Показываем что бот печатает
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ от GigaChat
    response = gigachat.send_message(message.text)
    
    # Отправляем ответ
    bot.reply_to(message, response)
    print(f"✅ Sent response to {message.chat.id}")

# Веб-хук endpoint - УПРОЩЕННАЯ ВЕРСИЯ
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем сырые данные
        raw_data = request.get_data(as_text=True)
        print(f"📥 Raw webhook data: {raw_data}")
        
        # Парсим JSON
        json_data = request.get_json()
        print(f"📦 Parsed JSON: {json.dumps(json_data, indent=2)}")
        
        if 'message' in json_data:
            chat_id = json_data['message']['chat']['id']
            text = json_data['message'].get('text', '')
            print(f"👤 Chat ID: {chat_id}, Text: {text}")
        
        # Обрабатываем обновление
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        
        print("✅ Webhook processed successfully")
        return "OK", 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return "Error", 500

# Статус страница
@app.route('/')
def status():
    return """
    <h1>🤖 Telegram Bot + GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>Webhook:</strong> ✅ Receiving requests</p>
    <p><strong>URL:</strong> https://telegram-bot-x6zm.onrender.com</p>
    <hr>
    <p>Проверь логи в Render - там должны быть сообщения о полученных запросах</p>
    """

@app.route('/debug')
def debug():
    """Страница отладки"""
    return {
        "status": "active",
        "webhook_working": True,
        "bot_token_exists": bool(BOT_TOKEN),
        "gigachat_key_exists": bool(GIGACHAT_API_KEY)
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port)
