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

# ОБРАБОТЧИК START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    print(f"🎯 Получен /start от {chat_id}")
    
    welcome_text = f"""
🎉 ПРИВЕТ! Я ТЕЛЕГРАМ БОТ С GIGACHAT!

🤖 Интеграция с GigaChat: {'✅ Активна' if gigachat.is_configured else '❌ Не настроена'}

💡 Просто напиши мне любое сообщение, и я обработаю его через нейросеть GigaChat!

🚀 Команды:
/start - это сообщение
/test - тест GigaChat
/status - статус системы

Напиши что-нибудь и увидишь ответ от GigaChat!
"""
    
    # ОТПРАВЛЯЕМ СООБЩЕНИЕ НАПРЯМУЮ ЧЕРЕЗ API
    success = send_telegram_message(chat_id, welcome_text)
    if success:
        print(f"✅ Приветствие отправлено в {chat_id}")
    else:
        print(f"❌ Не удалось отправить приветствие в {chat_id}")

# ОБРАБОТЧИК TEST
@bot.message_handler(commands=['test'])
def test_gigachat(message):
    chat_id = message.chat.id
    print(f"🧪 Тест GigaChat от {chat_id}")
    
    test_response = gigachat.get_response("Тестовое сообщение")
    send_telegram_message(chat_id, test_response)

# ОБРАБОТЧИК STATUS
@bot.message_handler(commands=['status'])
def send_status(message):
    chat_id = message.chat.id
    status_text = f"""
📊 СТАТУС СИСТЕМЫ:

🤖 Бот: ✅ Активен
🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
🌐 Веб-хук: ✅ Установлен

💬 Обработано сообщений: В работе...
"""
    send_telegram_message(chat_id, status_text)

# ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text
    
    print(f"💬 Сообщение от {chat_id}: {text}")
    
    # Игнорируем команды (они обрабатываются отдельно)
    if text.startswith('/'):
        return
    
    # Получаем ответ от GigaChat
    giga_response = gigachat.get_response(text)
    
    # Отправляем ответ
    send_telegram_message(chat_id, giga_response)
    print(f"✅ Ответ отправлен в {chat_id}")

# Веб-хук endpoint - ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ
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
        
        # Создаем Update объект и обрабатываем его
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        
        print("✅ Сообщение обработано")
        return "OK", 200
        
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        import traceback
        traceback.print_exc()
        return "Error", 500

# Альтернативный веб-хук для прямой обработки
@app.route('/webhook_direct', methods=['POST'])
def webhook_direct():
    """Альтернативный веб-хук с прямой обработкой"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            print(f"📨 Прямая обработка: {chat_id} -> {text}")
            
            # Обработка команд
            if text == '/start':
                welcome_text = "🎉 ПРИВЕТ! Я работаю через прямой веб-хук!"
                send_telegram_message(chat_id, welcome_text)
            elif text.startswith('/'):
                send_telegram_message(chat_id, f"🔧 Команда '{text}' обработана")
            else:
                # Обычные сообщения
                response = gigachat.get_response(text)
                send_telegram_message(chat_id, response)
        
        return "OK", 200
        
    except Exception as e:
        print(f"❌ Ошибка прямого веб-хука: {e}")
        return "Error", 500

# Статус страница
@app.route('/')
def home():
    return """
    <h1>🤖 Telegram Bot + GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>Webhook:</strong> ✅ Set</p>
    <p>Отправь боту <code>/start</code> в Telegram!</p>
    <p><a href="/test">Тест отправки сообщения</a></p>
    """

# Ручная отправка сообщения для теста
@app.route('/send_test')
def send_test_message():
    """Ручная отправка тестового сообщения"""
    chat_id = request.args.get('chat_id', '531129264')  # Ваш chat_id по умолчанию
    test_text = "🔧 Тест из веб-интерфейса! Бот работает!"
    success = send_telegram_message(chat_id, test_text)
    return jsonify({"status": "sent" if success else "failed", "chat_id": chat_id})

@app.route('/test')
def test_page():
    return """
    <h2>Тест бота</h2>
    <p><a href="/send_test?chat_id=531129264">Отправить тестовое сообщение</a></p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
