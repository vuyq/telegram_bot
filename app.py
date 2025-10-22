import os
import telebot
from flask import Flask, request, jsonify
import json
import requests
import time
import base64
import ssl
from pathlib import Path
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_AUTH = os.environ.get('GIGACHAT_AUTH')
APP_URL = "https://telegram-bot-x6zm.onrender.com"

# Настройки сертификатов
CERT_PATH = os.getenv("CERT_PATH", "./cert.pem")
CERT_URL = os.getenv("CERT_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("🚀 Бот запускается...")
print(f"🔑 Токен: {'✅' if BOT_TOKEN else '❌'}")
print(f"🧠 GigaChat Auth: {'✅' if GIGACHAT_AUTH else '❌'}")
print(f"📜 CERT_PATH: {CERT_PATH}")
print(f"🔗 CERT_URL: {'✅' if CERT_URL else '❌'}")

# Устанавливаем веб-хук
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{APP_URL}/webhook")
    print(f"✅ Веб-хук установлен: {APP_URL}/webhook")
except Exception as e:
    print(f"❌ Ошибка веб-хука: {e}")

class Config:
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    CERT_PATH = CERT_PATH
    CERT_URL = CERT_URL
    GIGACHAT_AUTH = GIGACHAT_AUTH

def download_certificate():
    """Загрузка SSL-сертификата при необходимости"""
    if Config.CERT_URL and not Path(Config.CERT_PATH).exists():
        try:
            response = requests.get(Config.CERT_URL, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            with open(Config.CERT_PATH, "wb") as f:
                f.write(response.content)
            print("✅ Сертификат успешно загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки сертификата: {e}")
            raise

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), 
      wait=wait_exponential(multiplier=1, min=2, max=10))
def get_gigachat_token() -> str:
    """Получение токена доступа GigaChat"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {Config.GIGACHAT_AUTH}'
    }
    payload = {'scope': 'GIGACHAT_API_PERS'}
    
    try:
        verify_ssl = Config.CERT_PATH if Path(Config.CERT_PATH).exists() else False
        print(f"🔐 Используем SSL проверку: {verify_ssl}")
        
        response = requests.post(
            url, 
            headers=headers, 
            data=payload, 
            verify=verify_ssl,
            timeout=Config.REQUEST_TIMEOUT
        )
        
        print(f"🔐 Статус аутентификации: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Токен GigaChat получен успешно")
                return access_token
            else:
                print("❌ Токен не найден в ответе")
        else:
            print(f"❌ Ошибка аутентификации: {response.status_code} - {response.text}")
            
        raise Exception(f"Ошибка получения токена: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка получения токена: {e}")
        raise

# КЛАСС GIGACHAT С ПРАВИЛЬНОЙ ИНИЦИАЛИЗАЦИЕЙ
class GigaChatBot:
    def __init__(self):
        self.is_configured = bool(GIGACHAT_AUTH)
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
        self.token_expires = 0
        
    def get_auth_token(self):
        """Получает токен авторизации для GigaChat"""
        try:
            # Проверяем, не истек ли текущий токен
            if self.access_token and time.time() < self.token_expires:
                return self.access_token
                
            print("🔐 Получаем новый токен GigaChat...")
            self.access_token = get_gigachat_token()
            # Токен действует 30 минут, устанавливаем время истечения на 25 минут
            self.token_expires = time.time() + 1500
            return self.access_token
            
        except Exception as e:
            print(f"❌ Ошибка получения токена: {e}")
            return None
    
    def _make_secure_request(self, method, url, **kwargs):
        """Выполняет безопасный запрос с сертификатами"""
        try:
            verify_ssl = Config.CERT_PATH if Path(Config.CERT_PATH).exists() else False
            kwargs['verify'] = verify_ssl
            kwargs['timeout'] = Config.REQUEST_TIMEOUT
            
            response = requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"❌ Ошибка безопасного запроса: {e}")
            # Пробуем без проверки SSL
            try:
                kwargs['verify'] = False
                response = requests.request(method, url, **kwargs)
                print("⚠️  Запрос выполнен без проверки SSL")
                return response
            except Exception as e2:
                print(f"❌ Критическая ошибка запроса: {e2}")
                raise
    
    def get_response(self, user_message):
        """Получает ответ от GigaChat"""
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_AUTH в настройках Render."
        
        try:
            auth_token = self.get_auth_token()
            if not auth_token:
                error_msg = """
❌ Не удалось авторизоваться в GigaChat. 

Возможные причины:
1. Неверный GIGACHAT_AUTH в настройках Render
2. Ключ не активирован в личном кабинете SberBank AI
3. Проблемы с сертификатами

💡 Для получения GIGACHAT_AUTH:
1. Перейдите на https://developers.sber.ru/studio/auth
2. Авторизуйтесь через СберID
3. Создайте новое приложение
4. Получите Client ID и Client Secret
5. Используйте их в формате base64(ClientID:ClientSecret)
"""
                return error_msg
            
            # Создаем промпт для специализации на международных отношениях
            system_prompt = """Ты - эксперт в области международных отношений. Твоя специализация включает:

🎓 **Образование и поступление:**
- Вузы для международных отношений (МГИМО, МГУ, СПбГУ, ВШЭ, РУДН)
- Вступительные экзамены и требования
- Программы обучения и специализации

📚 **Основные понятия:**
- Дипломатия и внешняя политика
- Международное право
- Геополитика и международная безопасность
- Глобализация и международные экономические отношения

💼 **Карьера:**
- Дипломатическая служба
- Международные организации (ООН, НАТО, ЕС, ВТО, МВФ)
- Международный бизнес
- Аналитические центры и СМИ

🌍 **Практические аспекты:**
- Современные международные конфликты
- Международные договоры и соглашения
- Внешняя политика России и других стран

Отвечай подробно, информативно, с конкретными примерами и практическими советами. Структурируй ответы для лучшего восприятия."""

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
            
            response = self._make_secure_request('POST', url, headers=headers, json=data)
            
            print(f"🧠 Статус ответа GigaChat: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                chat_response = result['choices'][0]['message']['content']
                print(f"✅ Ответ GigaChat получен: {len(chat_response)} символов")
                return chat_response
            elif response.status_code == 401:
                print("❌ Ошибка 401: Неавторизован")
                # Сбрасываем токен при ошибке авторизации
                self.access_token = None
                return "❌ Ошибка авторизации GigaChat. Попробуйте еще раз."
            elif response.status_code == 403:
                print("❌ Ошибка 403: Доступ запрещен")
                return "❌ Доступ к GigaChat запрещен. Проверьте права доступа API ключа."
            else:
                print(f"❌ Ошибка GigaChat API: {response.status_code} - {response.text}")
                return f"❌ Ошибка GigaChat API ({response.status_code}). Попробуйте позже."
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети GigaChat: {e}")
            return "❌ Ошибка соединения с GigaChat. Попробуйте позже."
        except Exception as e:
            print(f"❌ Общая ошибка GigaChat: {e}")
            return f"❌ Ошибка обработки запроса: {str(e)}"

# Инициализируем сертификаты и GigaChat
try:
    download_certificate()
    gigachat = GigaChatBot()
    print("✅ GigaChat инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации: {e}")
    gigachat = GigaChatBot()

# ФУНКЦИЯ ДЛЯ ОТПРАВКИ СООБЩЕНИЙ ЧЕРЕЗ API TELEGRAM
def send_telegram_message(chat_id, text):
    """Отправляет сообщение через Telegram Bot API"""
    try:
        max_length = 4000
        if len(text) > max_length:
            parts = []
            while text:
                if len(text) <= max_length:
                    parts.append(text)
                    break
                else:
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
                response = requests.post(url, json=data, timeout=10)
                if response.status_code != 200:
                    print(f"❌ Ошибка отправки части {i+1}: {response.text}")
                time.sleep(0.5)
            return True
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=data, timeout=10)
            success = response.status_code == 200
            if not success:
                print(f"❌ Ошибка Telegram API: {response.text}")
            return success
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

# ВЕБ-ХУК С РУЧНОЙ ОБРАБОТКОЙ
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        if request.content_type != 'application/json':
            return "Invalid content-type", 400
            
        json_data = request.get_json()
        if not json_data:
            return "Empty JSON", 400
        
        print(f"📥 Получен webhook")
        
        if 'message' in json_data:
            message = json_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message.get('from', {}).get('first_name', 'Пользователь')
            
            print(f"💬 Сообщение от {user_name}: {text}")
            
            if text == '/start':
                welcome_text = f"""
🌍 ДОБРО ПОЖАЛОВАТЬ В БОТ ПО МЕЖДУНАРОДНЫМ ОТНОШЕНИЯМ, {user_name}!

🎯 Я специализируюсь на международных отношениях и использую нейросеть GigaChat для ответов на ваши вопросы.

📚 Я могу помочь с:
• 🎓 Поступлением в вузы (МГИМО, МГУ, СПбГУ, ВШЭ, РУДН)
• 📖 Основными понятиями международных отношений
• 💼 Карьерными возможностями в этой сфере
• 🏛️ Международными организациями (ООН, НАТО, ЕС, ВТО)
• 🌐 Современными геополитическими процессами

💡 Просто задайте вопрос о международных отношениях, и GigaChat даст развернутый профессиональный ответ!

📋 Примеры вопросов:
"Какие экзамены нужны для поступления в МГИМО?"
"Объясни понятие 'дипломатический иммунитет'"
"Где можно работать после международных отношений?"
"Расскажи о структуре и функциях ООН"
"Какие языки важно знать международнику?"

🚀 Начните с любого вопроса!
"""
                send_telegram_message(chat_id, welcome_text)
                print(f"✅ Приветствие отправлено для {user_name}")
            
            elif text == '/help':
                help_text = """
❓ ПОМОЩЬ ПО БОТУ МЕЖДУНАРОДНЫХ ОТНОШЕНИЙ

🎯 Я использую нейросеть GigaChat для ответов на вопросы по:
• 🎓 Поступлению в вузы международных отношений
• 📚 Теории международных отношений
• 💼 Карьерным возможностям и профессиям
• 🏛️ Международным организациям
• 🌍 Современной геополитике

💡 Как задавать вопросы:
Будьте конкретны - так GigaChat даст более точный и полезный ответ.

📋 Примеры хороших вопросов:
"Какие предметы ЕГЭ нужны для МГИМО на факультет международных отношений?"
"В чем разница между дипломатией и внешней политикой?"
"Какие карьерные перспективы у выпускников международных отношений?"
"Расскажи о роли ООН в современном мире"
"Как изменилась геополитика после 2022 года?"

⚡ Просто напишите ваш вопрос - и получите развернутый ответ от GigaChat!

🔄 Если возникли проблемы - используйте /status для проверки системы.
"""
                send_telegram_message(chat_id, help_text)
            
            elif text == '/status':
                status_text = f"""
📊 СТАТУС СИСТЕМЫ:

🤖 Бот: ✅ Активен
🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
📜 Сертификаты: {'✅' if Path(CERT_PATH).exists() or CERT_URL else '❌'}
🌐 Веб-хук: ✅ Работает
💬 Пользователь: {user_name}

💡 Тестируем подключение к GigaChat...
"""
                send_telegram_message(chat_id, status_text)
                
                # Тестовый запрос
                test_response = gigachat.get_response("Ответь кратко: работает ли соединение?")
                status_text = f"🔧 Тест GigaChat: {'✅ Успешно' if 'Ошибка' not in test_response else '❌ Ошибка'}"
                if 'Ошибка' not in test_response:
                    status_text += f"\n\n📝 Пример ответа: {test_response[:100]}..."
                send_telegram_message(chat_id, status_text)
            
            elif text and not text.startswith('/'):
                # Показываем, что бот печатает
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
                    data = {"chat_id": chat_id, "action": "typing"}
                    requests.post(url, json=data, timeout=5)
                except:
                    pass
                
                print(f"🧠 Запрос к GigaChat от {user_name}: {text}")
                giga_response = gigachat.get_response(text)
                send_telegram_message(chat_id, giga_response)
                print(f"✅ Ответ GigaChat отправлен для {user_name}")
            
            else:
                print(f"⚠️  Игнорируем сообщение: {text}")
        
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
            "certificate_configured": Path(CERT_PATH).exists() or bool(CERT_URL),
            "test_message": test_message,
            "response": response,
            "response_length": len(response) if response else 0
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
    <p><strong>SSL Certificates:</strong> {}</p>
    <p><strong>GigaChat:</strong> {}</p>
    
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
    
    <p>Отправьте /start боту в Telegram!</p>
    """.format(
        '✅ Configured' if Path(CERT_PATH).exists() or CERT_URL else '❌ Not configured',
        '✅ Configured' if gigachat.is_configured else '❌ Not configured'
    )

@app.route('/status')
def status():
    return jsonify({
        "bot_status": "active",
        "gigachat_configured": gigachat.is_configured,
        "certificate_configured": Path(CERT_PATH).exists() or bool(CERT_URL),
        "webhook_set": True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Сервер запущен на порту {port}")
    print(f"🔐 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}")
    print(f"📜 Сертификаты: {'✅ Настроены' if Path(CERT_PATH).exists() or CERT_URL else '❌ Не настроены'}")
    
    # Тестовый запрос
    if gigachat.is_configured:
        print("🧪 Тестируем GigaChat...")
        try:
            test_response = gigachat.get_response("Тестовое сообщение")
            print(f"✅ GigaChat тест: {'Успешно' if 'Ошибка' not in test_response else 'Ошибка'}")
            if 'Ошибка' not in test_response:
                print(f"📄 Ответ: {test_response[:100]}...")
        except Exception as e:
            print(f"❌ GigaChat тест: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
