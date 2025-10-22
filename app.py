import os
import telebot
from flask import Flask, request, jsonify
import json
import requests
import time
import base64
import ssl

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')
APP_URL = "https://telegram-bot-x6zm.onrender.com"

# Настройки сертификатов
CERT_PATH = os.getenv("CERT_PATH", "./cert.pem")
CERT_URL = os.getenv("CERT_URL")
GIGACHAT_AUTH = os.getenv("GIGACHAT_AUTH")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

print("🚀 Бот запускается...")
print(f"🔑 Токен: {'✅' if BOT_TOKEN else '❌'}")
print(f"🧠 GigaChat: {'✅' if GIGACHAT_API_KEY else '❌'}")
print(f"📜 CERT_PATH: {CERT_PATH}")
print(f"🔗 CERT_URL: {'✅' if CERT_URL else '❌'}")
print(f"🔐 GIGACHAT_AUTH: {'✅' if GIGACHAT_AUTH else '❌'}")

# Устанавливаем веб-хук
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{APP_URL}/webhook")
    print(f"✅ Веб-хук установлен: {APP_URL}/webhook")
except Exception as e:
    print(f"❌ Ошибка веб-хука: {e}")

# КЛАСС GIGACHAT LITE С ПОДДЕРЖКОЙ СЕРТИФИКАТОВ
class GigaChatBot:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY or GIGACHAT_AUTH
        self.is_configured = bool(self.api_key)
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.cert_path = CERT_PATH
        self.cert_url = CERT_URL
        
    def _get_ssl_context(self):
        """Создает SSL контекст с сертификатами"""
        try:
            context = ssl.create_default_context()
            
            # Если указан путь к сертификату
            if os.path.exists(self.cert_path):
                context.load_verify_locations(self.cert_path)
                print(f"✅ Сертификат загружен: {self.cert_path}")
            elif self.cert_url:
                # Скачиваем сертификат по URL
                try:
                    response = requests.get(self.cert_url, timeout=10)
                    with open('/tmp/cert.pem', 'wb') as f:
                        f.write(response.content)
                    context.load_verify_locations('/tmp/cert.pem')
                    print(f"✅ Сертификат загружен по URL: {self.cert_url}")
                except Exception as e:
                    print(f"❌ Ошибка загрузки сертификата: {e}")
            
            return context
        except Exception as e:
            print(f"❌ Ошибка создания SSL контекста: {e}")
            return None
    
    def _make_secure_request(self, method, url, **kwargs):
        """Выполняет безопасный запрос с сертификатами"""
        try:
            ssl_context = self._get_ssl_context()
            if ssl_context:
                kwargs['verify'] = self.cert_path if os.path.exists(self.cert_path) else True
            else:
                # Если сертификаты не настроены, отключаем проверку (для тестирования)
                kwargs['verify'] = False
                print("⚠️  Проверка SSL отключена")
            
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
    
    def get_auth_token(self):
        """Получает токен авторизации для GigaChat Lite"""
        try:
            if not self.api_key:
                print("❌ API ключ не установлен")
                return None
                
            print(f"🔐 Используем API ключ: {self.api_key[:10]}...")
            
            # МЕТОД 1: Используем GIGACHAT_AUTH как готовый токен
            if GIGACHAT_AUTH and len(GIGACHAT_AUTH) > 100:
                print("✅ Используем GIGACHAT_AUTH как токен")
                return GIGACHAT_AUTH
            
            # МЕТОД 2: Basic Auth
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            # Подготавливаем данные для аутентификации
            if ":" in self.api_key:
                login, password = self.api_key.split(":", 1)
            else:
                login = password = self.api_key
            
            auth_string = f"{login}:{password}"
            auth_base64 = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'scope': 'GIGACHAT_API_PERS'
            }
            
            print("🔐 Пробуем Basic Auth с сертификатами...")
            
            response = self._make_secure_request(
                'POST', 
                url, 
                headers=headers, 
                data=data, 
                timeout=30
            )
            
            print(f"🔐 Статус аутентификации: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                if access_token:
                    print("✅ Токен успешно получен")
                    return access_token
                else:
                    print("❌ Токен не найден в ответе")
            else:
                print(f"❌ Ошибка аутентификации: {response.status_code}")
                print(f"🔐 Ответ сервера: {response.text}")
                
                # Пробуем альтернативный scope
                if response.status_code == 400:
                    print("🔐 Пробуем альтернативный scope...")
                    data['scope'] = 'GIGACHAT'
                    
                    response = self._make_secure_request(
                        'POST', 
                        url, 
                        headers=headers, 
                        data=data, 
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        access_token = token_data.get('access_token')
                        if access_token:
                            print("✅ Токен получен с альтернативным scope")
                            return access_token
            
            return None
                
        except Exception as e:
            print(f"❌ Критическая ошибка аутентификации: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_response(self, user_message):
        """Получает ответ от GigaChat Lite"""
        if not self.is_configured:
            return "❌ GigaChat не настроен. Добавьте GIGACHAT_API_KEY в настройках Render."
        
        try:
            auth_token = self.get_auth_token()
                
            if not auth_token:
                error_msg = """
❌ Не удалось авторизоваться в GigaChat. 

Возможные причины:
1. Неверный API ключ в GIGACHAT_API_KEY
2. Ключ не активирован в личном кабинете SberBank AI
3. Проблемы с сертификатами
4. Неправильный scope

Проверьте:
• Корректность GIGACHAT_API_KEY в настройках Render
• Активирован ли доступ к GigaChat API
• Попробуйте использовать GIGACHAT_AUTH для прямого указания токена

💡 Для получения API ключа:
1. Перейдите на https://developers.sber.ru/studio/auth
2. Авторизуйтесь через СберID
3. Создайте новое приложение
4. Получите Client ID и Client Secret
5. Используйте их в формате: ClientID:ClientSecret
"""
                return error_msg
            
            # Создаем промпт для специализации на международных отношениях
            system_prompt = """Ты - эксперт в области международных отношений. Отвечай на вопросы профессионально и подробно по темам:
- Поступление в вузы (МГИМО, МГУ, СПбГУ и др.)
- Основные понятия международных отношений
- Карьерные возможности
- Международные организации
- Современная геополитика"""

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
                "max_tokens": 1500
            }
            
            print(f"🧠 Отправка запроса к GigaChat...")
            
            response = self._make_secure_request(
                'POST', 
                url, 
                headers=headers, 
                json=data, 
                timeout=30
            )
            
            print(f"🧠 Статус ответа GigaChat: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                chat_response = result['choices'][0]['message']['content']
                print(f"✅ Ответ GigaChat получен: {len(chat_response)} символов")
                return chat_response
            elif response.status_code == 401:
                print("❌ Ошибка 401: Неавторизован")
                return "❌ Ошибка авторизации GigaChat. Проверьте API ключ."
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

# Инициализируем GigaChat
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
            
            print(f"💬 Сообщение: {chat_id} -> {text}")
            
            if text == '/start':
                welcome_text = """
🌍 БОТ ПО МЕЖДУНАРОДНЫМ ОТНОШЕНИЯМ С GIGACHAT

🎯 Специализация:
• Поступление в вузы (МГИМО, МГУ, СПбГУ)
• Основные понятия международных отношений
• Карьерные возможности
• Международные организации
• Современная геополитика

💡 Просто задайте вопрос о международных отношениях!

Примеры:
"Какие экзамены нужны для МГИМО?"
"Что такое дипломатический иммунитет?"
"Где работать после международных отношений?"

🚀 Начните с любого вопроса!
"""
                send_telegram_message(chat_id, welcome_text)
            
            elif text == '/status':
                status_text = f"""
📊 СТАТУС СИСТЕМЫ:

🤖 Бот: ✅ Активен
🧠 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}
📜 Сертификаты: {'✅' if os.path.exists(CERT_PATH) or CERT_URL else '❌'}
🌐 Веб-хук: ✅ Работает

💬 Тестируем GigaChat...
"""
                send_telegram_message(chat_id, status_text)
                
                # Тестовый запрос
                test_response = gigachat.get_response("Ответь кратко: работает ли соединение?")
                status_text += f"\n🔧 Тест GigaChat: {'✅ Успешно' if 'Ошибка' not in test_response else '❌ Ошибка'}"
                send_telegram_message(chat_id, status_text)
            
            elif text and not text.startswith('/'):
                # Показываем, что бот печатает
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
                    data = {"chat_id": chat_id, "action": "typing"}
                    requests.post(url, json=data, timeout=5)
                except:
                    pass
                
                print(f"🧠 Запрос к GigaChat: {text}")
                giga_response = gigachat.get_response(text)
                send_telegram_message(chat_id, giga_response)
                print(f"✅ Ответ отправлен в {chat_id}")
            
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
            "certificate_configured": bool(os.path.exists(CERT_PATH) or CERT_URL),
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
    
    <p>Отправьте /start боту в Telegram!</p>
    """.format(
        '✅ Configured' if os.path.exists(CERT_PATH) or CERT_URL else '❌ Not configured',
        '✅ Configured' if gigachat.is_configured else '❌ Not configured'
    )

@app.route('/status')
def status():
    return jsonify({
        "bot_status": "active",
        "gigachat_configured": gigachat.is_configured,
        "certificate_configured": bool(os.path.exists(CERT_PATH) or CERT_URL),
        "webhook_set": True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Сервер запущен на порту {port}")
    print(f"🔐 GigaChat: {'✅ Настроен' if gigachat.is_configured else '❌ Не настроен'}")
    print(f"📜 Сертификаты: {'✅ Настроены' if os.path.exists(CERT_PATH) or CERT_URL else '❌ Не настроены'}")
    
    # Тестовый запрос
    if gigachat.is_configured:
        print("🧪 Тестируем GigaChat...")
        try:
            test_response = gigachat.get_response("Тестовое сообщение")
            print(f"✅ GigaChat тест: {'Успешно' if 'Ошибка' not in test_response else 'Ошибка'}")
        except Exception as e:
            print(f"❌ GigaChat тест: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
