import json
import os
import logging
import requests

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

BOT_TOKEN = os.environ['BOT_TOKEN']

def handler(event, context):
    """
    Основной обработчик для Yandex Cloud Functions
    """
    try:
        # Логируем входящий запрос
        logger.info(f"Received event: {event}")
        
        # Парсим тело запроса
        body = json.loads(event['body'])
        
        # Обрабатываем сообщение
        if 'message' in body:
            process_message(body['message'])
        elif 'callback_query' in body:
            process_callback(body['callback_query'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_message(message):
    """Обработка входящих сообщений"""
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_name = message['from'].get('first_name', 'Пользователь')
    
    logger.info(f"Processing message from {user_name}: {text}")
    
    # Обработка команд
    commands = {
        '/start': f'Привет, {user_name}! Я бот на Яндекс Облаке! 🚀',
        '/help': 'Доступные команды:\n/start - начать работу\n/help - помощь\n/info - информация',
        '/info': 'Этот бот работает на Yandex Cloud Functions с Python'
    }
    
    response_text = commands.get(text, f'Вы написали: {text}')
    send_telegram_message(chat_id, response_text)

def process_callback(callback_query):
    """Обработка callback запросов от inline кнопок"""
    chat_id = callback_query['message']['chat']['id']
    data = callback_query['data']
    
    send_telegram_message(chat_id, f'Обработан callback: {data}')

def send_telegram_message(chat_id, text):
    """Отправка сообщения через Telegram API"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Message sent to {chat_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message: {str(e)}")