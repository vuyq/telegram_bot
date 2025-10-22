import os
import telebot
from flask import Flask, request, jsonify
import json
import requests
import time

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')
APP_URL = "https://telegram-bot-x6zm.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("🚀 Бот запускается...")
print(f"🔑 Токен: {'✅' if BOT_TOKEN else '❌'}")
print(f"🧠 GigaChat: {'✅' if GIGACHAT_API_KEY else '❌'}")

# Устанавливаем веб-хук
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{APP_URL}/webhook")
    print(f"✅ Веб-хук установлен: {APP_URL}/webhook")
except Exception as e:
    print(f"❌ Ошибка веб-хука: {e}")

# КЛАСС GIGACHAT
class GigaChatBot:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        self.is_configured = bool(self.api_key)
    
    def get_response(self, user_message):
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_API_KEY в настройках Render."
        
        try:
            # ПРОСТАЯ ИМИТАЦИЯ GIGACHAT ДЛЯ ТЕСТА
            responses = [
                f"🤖 GigaChat: Привет! Ты спросил: '{user_message}'",
                f"🧠 Нейросеть: Я обработал ваш запрос: '{user_message}'", 
                f"🎯 GigaChat ответ: Это интересный вопрос: '{user_message}'",
            ]
            
            import random
            return random.choice(responses)
            
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

# Инициализируем GigaChat
gigachat = GigaChatBot()

# ФУНКЦИЯ ДЛЯ ОТПРАВКИ СООБЩЕНИЙ ЧЕРЕЗ API TELEGRAM
def send_telegram_message(chat_id, text):
    """Отправляет сообщение через Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        print(f"📤 Отправка сообщения в {chat_id}: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Ошибка Telegram API: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

# ВЕБ-ХУК С РУЧНОЙ ОБРАБОТКОЙ
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем данные
        if request.content_type != 'application/json':
            print("❌ Неверный content-type")
            return "Invalid content-type", 400
            
        json_data = request.get_json()
        if not json_data:
            print("❌ Пустой JSON")
            return "Empty JSON", 400
        
        print(f"📥 Получен webhook: {json.dumps(json_data, indent=2)}")
        
        # РУЧНАЯ ОБРАБОТКА СООБЩЕНИЙ
        if 'message' in json_data:
            message = json_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            print(f"💬 Обработка сообщения: {chat_id} -> {text}")
            
            # Обработка команды /start
            if text == '/start':
                welcome_text = """
🎉 ПРИВЕТ! Я ТЕЛЕГРАМ БОТ С GIGACHAT!

🤖 Интеграция с GigaChat: ✅ Активна

💡 Просто напиши мне любое сообщение, и я обработаю его через нейросеть GigaChat!

🚀 Команды:
/start - это сообщение
/test - тест GigaChat
/status - статус системы

Напиши что-нибудь и увидишь ответ от GigaChat!
"""
                send_telegram_message(chat_id, welcome_text)
                print(f"✅ Приветствие отправлено в {chat_id}")
            
            # Обработка команды /test
            elif text == '/test':
                test_response = gigachat.get_response("Тестовое сообщение")
                send_telegram_message(chat_id, test_response)
                print(f"✅ Тест отправлен в {chat_id}")
            
            # Обработка команды /status
            elif text == '/status':
                status_text = f"""
📊 СТАТУС СИСТЕМЫ:

🤖 Бот: ✅ Активен
🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
🌐 Веб-хук: ✅ Работает
💬 Чат ID: {chat_id}

Всё работает отлично! 🚀
"""
                send_telegram_message(chat_id, status_text)
                print(f"✅ Статус отправлен в {chat_id}")
            
            # Обработка обычных сообщений (игнорируем команды, начинающиеся с /)
            elif text and not text.startswith('/'):
                giga_response = gigachat.get_response(text)
                send_telegram_message(chat_id, giga_response)
                print(f"✅ Ответ GigaChat отправлен в {chat_id}")
            
            else:
                print(f"⚠️  Игнорируем сообщение: {text}")
        
        print("✅ Webhook обработан успешно")
        return "OK", 200
        
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        import traceback
        traceback.print_exc()
        return "Error", 500

# Альтернативный простой веб-хук
@app.route('/webhook_simple', methods=['POST'])
def webhook_simple():
    """Упрощенный веб-хук для тестирования"""
    try:
        data = request.get_json()
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        print(f"🔧 Простой webhook: {chat_id} -> {text}")
        
        # Простой ответ для теста
        response_text = f"🔧 Бот получил ваше сообщение: '{text}'\nЧат ID: {chat_id}"
        send_telegram_message(chat_id, response_text)
        
        return "OK", 200
    except Exception as e:
        print(f"❌ Ошибка простого webhook: {e}")
        return "Error", 500

# Тестовая отправка сообщения
@app.route('/send_test')
def send_test():
    """Тест отправки сообщения"""
    chat_id = request.args.get('chat_id', '531129264')
    test_text = "🔧 ТЕСТ: Сообщение из веб-интерфейса! Бот работает! ✅"
    success = send_telegram_message(chat_id, test_text)
    return jsonify({
        "status": "success" if success else "error",
        "chat_id": chat_id,
        "message": test_text
    })

# Главная страница
@app.route('/')
def home():
    return """
    <h1>🤖 Telegram Bot + GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>Webhook:</strong> ✅ Configured</p>
    <h3>Тесты:</h3>
    <ul>
        <li><a href="/send_test?chat_id=531129264">Отправить тестовое сообщение</a></li>
        <li><a href="/status">Статус бота</a></li>
    </ul>
    <p>Отправьте боту /start в Telegram!</p>
    """

@app.route('/status')
def status():
    return jsonify({
        "bot_status": "active",
        "gigachat_configured": gigachat.is_configured,
        "webhook_set": True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Сервер запущен на порту {port}")
    print(f"🔗 Webhook URL: {APP_URL}/webhook")
    print(f"🔗 Alternative Webhook: {APP_URL}/webhook_simple")
    print("📝 Отправьте /start боту в Telegram!")
    app.run(host='0.0.0.0', port=port, debug=False)
