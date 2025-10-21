import os
import requests
import json
from flask import Flask, request
import telebot

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
APP_URL = "https://your-app-name.onrender.com"  # ЗАМЕНИТЕ на ваш URL
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')  # Добавьте эту переменную в Render

# Инициализация бота и приложения
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

class GigaChatAPI:
    def __init__(self, client_secret):
        self.client_secret = client_secret
        self.access_token = None
        self.get_access_token()
    
    def get_access_token(self):
        """Получение токена доступа для GigaChat API"""
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': '6f0b1291-c7f3-43c6-bb2e-9f3efb2dc98e',  # Можно оставить или сгенерировать свой
            }
            data = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            # Используем авторизацию через client credentials
            auth = ('client', 'client')  # Базовые креденшилы, могут меняться
            response = requests.post(
                url, 
                headers=headers, 
                data=data, 
                auth=auth,
                verify=False  # Внимание: для продакшена нужно правильно настроить SSL
            )
            
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                return True
            else:
                print(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Исключение при получении токена: {e}")
            return False
    
    def send_message(self, message_text):
        """Отправка сообщения в GigaChat и получение ответа"""
        if not self.access_token:
            if not self.get_access_token():
                return "Ошибка: не удалось получить доступ к GigaChat API"
        
        try:
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }
            
            data = {
                "model": "GigaChat",  # или "GigaChat-Plus" для более продвинутой модели
                "messages": [
                    {
                        "role": "user",
                        "content": message_text
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(url, headers=headers, json=data, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 401:
                # Токен истек, пробуем обновить
                self.get_access_token()
                return self.send_message(message_text)
            else:
                return f"Ошибка API GigaChat: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Ошибка при обращении к GigaChat: {str(e)}"

# Инициализация GigaChat (только если указан API ключ)
gigachat = None
if GIGACHAT_API_KEY:
    gigachat = GigaChatAPI(GIGACHAT_API_KEY)

# Обработчики Telegram бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🤖 Привет! Я бот с интеграцией GigaChat.

Просто напишите мне любой вопрос или сообщение, и я обработаю его с помощью нейросети!

Доступные команды:
/start - показать это сообщение
/giga [текст] - обратиться к GigaChat
/help - помощь
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 Помощь по боту:

• Просто отправьте любое текстовое сообщение - бот ответит через GigaChat
• Или используйте команду /giga [ваш вопрос]

Пример:
/giga Напиши код Python для сортировки списка

Бот работает на основе нейросети GigaChat от Сбера.
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['giga'])
def giga_chat_command(message):
    """Обработка команды /giga"""
    if not gigachat:
        bot.reply_to(message, "❌ GigaChat не настроен. Проверьте API ключ.")
        return
    
    # Извлекаем текст после команды
    command_text = message.text.split(' ', 1)
    if len(command_text) < 2:
        bot.reply_to(message, "❌ Пожалуйста, укажите ваш вопрос после команды /giga")
        return
    
    user_message = command_text[1]
    
    # Отправляем сообщение о обработке
    processing_msg = bot.reply_to(message, "🔄 Обрабатываю запрос GigaChat...")
    
    # Получаем ответ от GigaChat
    response = gigachat.send_message(user_message)
    
    # Отправляем ответ (разбиваем на части если слишком длинный)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            bot.edit_message_text(
                response[i:i+4000], 
                message.chat.id, 
                processing_msg.message_id
            )
    else:
        bot.edit_message_text(
            response, 
            message.chat.id, 
            processing_msg.message_id
        )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех текстовых сообщений"""
    if not gigachat:
        bot.reply_to(message, "❌ GigaChat не настроен. Проверьте API ключ.")
        return
    
    # Игнорируем команды без слеша
    if message.text.startswith('/'):
        return
    
    # Отправляем сообщение о обработке
    processing_msg = bot.reply_to(message, "🔄 Обрабатываю запрос...")
    
    # Получаем ответ от GigaChat
    response = gigachat.send_message(message.text)
    
    # Отправляем ответ
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            if i == 0:
                bot.edit_message_text(
                    response[i:i+4000], 
                    message.chat.id, 
                    processing_msg.message_id
                )
            else:
                bot.send_message(message.chat.id, response[i:i+4000])
    else:
        bot.edit_message_text(
            response, 
            message.chat.id, 
            processing_msg.message_id
        )

# Веб-хук для Render
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/' + BOT_TOKEN)
    
    status = "✅ Бот активен!"
    if not gigachat:
        status += " ❌ GigaChat не настроен"
    else:
        status += " ✅ GigaChat подключен"
    
    return status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
