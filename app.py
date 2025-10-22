iimport os
import telebot
from flask import Flask, request
import json

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
    bot.set_webhook(url=f"{APP_URL}/webhook")
    print("✅ Веб-хук установлен")
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
            # ЗАМЕНИ ЭТУ ЧАСТЬ НА РЕАЛЬНЫЙ API GIGACHAT
            
            responses = [
                f"🤖 GigaChat: Привет! Ты спросил: '{user_message}'",
                f"🧠 Нейросеть: Я обработал ваш запрос: '{user_message}'", 
                f"🎯 GigaChat ответ: Это интересный вопрос: '{user_message}'",
                f"💡 ИИ: По вашему запросу '{user_message}' я могу помочь!",
                f"🚀 GigaChat: Отличный вопрос! '{user_message}'"
            ]
            
            import random
            return random.choice(responses)
            
        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

# Инициализируем GigaChat
gigachat = GigaChatBot()

# ОБРАБОТЧИК START С GIGACHAT
@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(f"🎯 Получен /start от {message.chat.id}")
    
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
    
    bot.send_message(message.chat.id, welcome_text)
    print(f"✅ Отправлено приветствие в чат {message.chat.id}")

# ОБРАБОТЧИК TEST С GIGACHAT
@bot.message_handler(commands=['test'])
def test_gigachat(message):
    print(f"🧪 Тест GigaChat от {message.chat.id}")
    
    test_response = gigachat.get_response("Тестовое сообщение для проверки GigaChat")
    bot.send_message(message.chat.id, test_response)

# ОБРАБОТЧИК STATUS
@bot.message_handler(commands=['status'])
def show_status(message):
    status_text = f"""
📊 СТАТУС СИСТЕМЫ:

• 🤖 Бот: ✅ Активен
• 🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
• 🌐 Сервер: {APP_URL}
• 🔑 API ключ: {'✅ Присутствует' if GIGACHAT_API_KEY else '❌ Отсутствует'}

💡 Для настройки GigaChat:
1. Получи API ключ на developers.sber.ru
2. Добавь GIGACHAT_API_KEY в Render
3. Обнови код для реальных API запросов
"""
    bot.send_message(message.chat.id, status_text)

# ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ С GIGACHAT
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    print(f"💬 Сообщение от {message.chat.id}: {message.text}")
    
    # Игнорируем команды
    if message.text.startswith('/'):
        return
    
    # Показываем "печатает..."
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ от GigaChat
    giga_response = gigachat.get_response(message.text)
    
    # Отправляем ответ
    bot.send_message(message.chat.id, giga_response)
    print(f"✅ Ответ GigaChat отправлен в чат {message.chat.id}")

# Веб-хук endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        
        # Логируем входящее сообщение
        if 'message' in json_data:
            chat_id = json_data['message']['chat']['id']
            text = json_data['message'].get('text', '')
            print(f"📥 Чат: {chat_id}, Текст: '{text}'")
        
        # Обрабатываем сообщение
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        
        print("✅ Сообщение обработано")
        return "OK", 200
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return "Error", 500

# Статус страница
@app.route('/')
def home():
    return f"""
    <h1>🤖 Telegram Bot + GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>GigaChat:</strong> {'✅ Configured' if gigachat.is_configured else '❌ Not configured'}</p>
    <p><strong>URL:</strong> {APP_URL}</p>
    <hr>
    <p>Отправь боту <code>/start</code> в Telegram!</p>
    <p>Или любое сообщение для теста GigaChat</p>
    """

@app.route('/gigachat_test')
def gigachat_test():
    """Тестовая страница для GigaChat"""
    test_response = gigachat.get_response("Тест из браузера")
    return f"""
    <h1>🧠 GigaChat Test</h1>
    <p><strong>Response:</strong> {test_response}</p>
    <p><strong>API Key:</strong> {'✅ Present' if GIGACHAT_API_KEY else '❌ Missing'}</p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
