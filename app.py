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

# КЛАСС GIGACHAT С РЕАЛЬНОЙ ИНТЕГРАЦИЕЙ
class GigaChatBot:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        self.is_configured = bool(self.api_key)
        self.access_token = None
        self.token_expires = 0
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        
    def get_auth_token(self):
        """Получает токен авторизации для GigaChat API"""
        try:
            if not self.api_key:
                return None
                
            # Проверяем, не истек ли текущий токен
            if self.access_token and time.time() < self.token_expires:
                return self.access_token
                
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            # Токен действует 30 минут, устанавливаем время истечения на 25 минут
            self.token_expires = time.time() + 1500
            
            print("✅ Токен GigaChat получен")
            return self.access_token
            
        except Exception as e:
            print(f"❌ Ошибка получения токена GigaChat: {e}")
            return None
    
    def get_response(self, user_message):
        """Получает ответ от GigaChat API"""
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_API_KEY в настройках Render."
        
        try:
            auth_token = self.get_auth_token()
            if not auth_token:
                return "❌ Не удалось авторизоваться в GigaChat. Проверьте API ключ."
            
            # Создаем промпт для специализации на международных отношениях
            system_prompt = """Ты - эксперт в области международных отношений. Твоя специализация:
1. Международные отношения и дипломатия
2. Поступление в вузы на международные отношения (МГИМО, МГУ, СПбГУ и др.)
3. Карьерные возможности в сфере международных отношений
4. Основные понятия и теории международных отношений
5. Международные организации (ООН, НАТО, ЕС, ВТО и др.)
6. Внешняя политика и геополитика

Отвечай подробно, информативно и профессионально. Давай конкретные примеры и практические советы.
Если вопрос не по теме международных отношений, вежливо направляй разговор в нужное русло."""

            url = f"{self.base_url}/chat/completions"
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            data = {
                "model": "GigaChat",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            print(f"🧠 Отправка запроса к GigaChat: {user_message[:100]}...")
            response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            chat_response = result['choices'][0]['message']['content']
            
            print(f"✅ Ответ GigaChat получен: {len(chat_response)} символов")
            return chat_response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети GigaChat: {e}")
            return "❌ Ошибка соединения с GigaChat. Попробуйте позже."
        except Exception as e:
            print(f"❌ Ошибка GigaChat API: {e}")
            return f"❌ Ошибка обработки запроса: {str(e)}"

# Инициализируем GigaChat
gigachat = GigaChatBot()

# ФУНКЦИЯ ДЛЯ ОТПРАВКИ СООБЩЕНИЙ ЧЕРЕЗ API TELEGRAM
def send_telegram_message(chat_id, text):
    """Отправляет сообщение через Telegram Bot API"""
    try:
        # Разбиваем длинные сообщения на части (Telegram ограничение 4096 символов)
        max_length = 4000
        if len(text) > max_length:
            parts = []
            while text:
                if len(text) <= max_length:
                    parts.append(text)
                    break
                else:
                    # Находим последний перенос строки в пределах лимита
                    split_pos = text.rfind('\n', 0, max_length)
                    if split_pos == -1:
                        split_pos = text.rfind('. ', 0, max_length)
                    if split_pos == -1:
                        split_pos = text.rfind(' ', 0, max_length)
                    if split_pos == -1:
                        split_pos = max_length
                    
                    parts.append(text[:split_pos])
                    text = text[split_pos:].lstrip()
            
            for i, part in enumerate(parts):
                part_text = f"{part}\n\n({i+1}/{len(parts)})"
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": part_text,
                    "parse_mode": "HTML"
                }
                requests.post(url, json=data, timeout=10)
                time.sleep(0.5)  # Небольшая задержка между сообщениями
            return True
        else:
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
🌍 ДОБРО ПОЖАЛОВАТЬ В БОТ ПО МЕЖДУНАРОДНЫМ ОТНОШЕНИЯМ!

🎯 Я специализируюсь на международных отношениях и использую нейросеть GigaChat для ответов на ваши вопросы.

📚 Я могу помочь с:
• Поступлением в вузы (МГИМО, МГУ, СПбГУ и др.)
• Основными понятиями международных отношений
• Карьерными возможностями в этой сфере
• Международными организациями (ООН, НАТО, ЕС и др.)
• Современными геополитическими процессами

💡 Просто задайте вопрос о международных отношениях, и GigaChat даст развернутый профессиональный ответ!

Примеры вопросов:
"Какие экзамены нужны для поступления на международные отношения в МГИМО?"
"Объясни понятие 'дипломатический иммунитет'"
"Где можно работать после окончания факультета международных отношений?"
"Расскажи о структуре ООН"

🚀 Начните с любого вопроса!
"""
                send_telegram_message(chat_id, welcome_text)
                print(f"✅ Приветствие отправлено в {chat_id}")
            
            # Обработка команды /help
            elif text == '/help':
                help_text = """
❓ **ПОМОЩЬ ПО БОТУ МЕЖДУНАРОДНЫХ ОТНОШЕНИЙ**

🎯 **Я использую нейросеть GigaChat для ответов на вопросы по:**
• Международным отношениям и дипломатии
• Поступлению в профильные вузы
• Карьерным возможностям
• Международным организациям
• Геополитике и внешней политике

💡 **Как задавать вопросы:**
Будьте конкретны - так GigaChat даст более точный ответ.

📋 **Примеры хороших вопросов:**
"Какие предметы ЕГЭ нужны для МГИМО на факультет международных отношений?"
"В чем разница между дипломатией и внешней политикой?"
"Какие карьерные перспективы у выпускников международных отношений?"
"Расскажи о роли ООН в современном мире"

⚡ **Просто напишите ваш вопрос - и получите развернутый ответ от GigaChat!**
"""
                send_telegram_message(chat_id, help_text)
            
            # Обработка команды /status
            elif text == '/status':
                status_text = f"""
📊 **СТАТУС СИСТЕМЫ:**

🤖 Бот: ✅ Активен
🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
🌐 Веб-хук: ✅ Работает
💬 Чат ID: {chat_id}

💡 **GigaChat API:** {'✅ Доступен' if gigachat.is_configured else '❌ Требуется настройка'}

Всё готово к работе! Задавайте вопросы по международным отношениям! 🎓🌍
"""
                send_telegram_message(chat_id, status_text)
            
            # Обработка обычных сообщений (игнорируем команды, начинающиеся с /)
            elif text and not text.startswith('/'):
                # Показываем, что бот печатает
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
                data = {"chat_id": chat_id, "action": "typing"}
                requests.post(url, json=data, timeout=5)
                
                print(f"🧠 Запрос к GigaChat: {text}")
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

# Тест GigaChat
@app.route('/test_gigachat')
def test_gigachat():
    """Тест подключения к GigaChat"""
    test_message = "Привет! Ответь кратко: что такое международные отношения?"
    try:
        response = gigachat.get_response(test_message)
        return jsonify({
            "status": "success",
            "gigachat_configured": gigachat.is_configured,
            "test_message": test_message,
            "response": response
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        })

# Главная страница
@app.route('/')
def home():
    return """
    <h1>🌍 Бот по международным отношениям с GigaChat</h1>
    <p><strong>Status:</strong> ✅ Active</p>
    <p><strong>AI:</strong> GigaChat Integration</p>
    <p><strong>Specialization:</strong> Международные отношения</p>
    
    <h3>Тесты:</h3>
    <ul>
        <li><a href="/test_gigachat">Тест GigaChat</a></li>
        <li><a href="/status">Статус системы</a></li>
    </ul>
    
    <h3>Функции:</h3>
    <ul>
        <li>🎓 Консультации по поступлению в вузы</li>
        <li>📚 Объяснение понятий международных отношений</li>
        <li>💼 Карьерные возможности</li>
        <li>🏛️ Международные организации</li>
        <li>🧠 Ответы от нейросети GigaChat</li>
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
    print(f"🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}")
    print(f"🎯 Специализация: Международные отношения")
    print("📝 Отправьте /start боту в Telegram!")
    
    # Тестовый запрос к GigaChat при запуске
    if gigachat.is_configured:
        print("🧪 Тестируем подключение к GigaChat...")
        try:
            test_response = gigachat.get_response("Привет! Ответь кратко одним предложением.")
            print(f"✅ GigaChat тест: Успешно ({len(test_response)} символов)")
        except Exception as e:
            print(f"❌ GigaChat тест: Ошибка - {e}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
