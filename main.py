import os
import time
import logging
import json
from datetime import datetime, timedelta, UTC
import msal
import requests
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from logging.handlers import RotatingFileHandler

# Загрузка переменных окружения
load_dotenv()

# Создание директории для логов
if not os.path.exists('logs'):
    os.makedirs('logs')

# Создание директории для данных
if not os.path.exists('data'):
    os.makedirs('data')

# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    # Форматтер для логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Создаем логгер
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Очищаем существующие обработчики
    logger.handlers = []
    
    # Обработчик для INFO уровня
    info_handler = RotatingFileHandler(
        'logs/info.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=15,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    
    # Обработчик для ERROR уровня
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=15,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Обработчик для DEBUG уровня
    debug_handler = RotatingFileHandler(
        'logs/debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=15,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Добавляем все обработчики
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)
    
    return logger

# Инициализация логгера
logger = setup_logging()

# Конфигурация приложения Azure AD
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
USER_ID = os.getenv('USER_ID')  # Добавляем ID пользователя

# Конфигурация Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки API Microsoft Graph
SCOPES = [
    'https://graph.microsoft.com/.default',
]
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'

# Инициализация Telegram бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Путь к файлу с уведомлениями
NOTIFICATIONS_FILE = os.path.join('data', 'sent_notifications.json')
# Путь к файлу с кэшем токена
TOKEN_CACHE_FILE = os.path.join('data', 'token_cache.json')

def load_notifications():
    """Загрузка информации об отправленных уведомлениях из JSON файла"""
    try:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла уведомлений: {e}")
        return {}

def save_notifications(notifications):
    """Сохранение информации об отправленных уведомлениях в JSON файл"""
    try:
        with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(notifications, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла уведомлений: {e}")

# Загружаем уведомления при запуске
sent_notifications = load_notifications()

def load_token_cache():
    """Загрузка кэша токена из JSON файла"""
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке кэша токена: {e}")
        return {}

def save_token_cache(token_data):
    """Сохранение кэша токена в JSON файл"""
    try:
        with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении кэша токена: {e}")

# Загружаем кэш токена при запуске
token_cache = load_token_cache()

async def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Сообщение успешно отправлено в Telegram: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")

def get_access_token():
    """Получение токена доступа через MSAL с использованием кэша"""
    try:
        # Проверяем наличие токена в кэше
        if token_cache:
            cached_token = token_cache.get('access_token')
            expires_at = datetime.fromisoformat(token_cache.get('expires_at', ''))
            current_time = datetime.now(UTC)
            
            # Если токен существует и не истек
            if cached_token and expires_at > current_time:
                logger.info("Используется кэшированный токен")
                return cached_token
        
        logger.debug(f"Попытка получения нового токена доступа. Authority: {AUTHORITY}")
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY
        )
        
        result = app.acquire_token_for_client(scopes=SCOPES)
        
        if 'access_token' in result:
            # Сохраняем токен в кэш
            expires_in = result.get('expires_in', 3600)  # По умолчанию 1 час
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in - 300)  # Вычитаем 5 минут для надежности
            
            token_cache_data = {
                'access_token': result['access_token'],
                'expires_at': expires_at.isoformat()
            }
            save_token_cache(token_cache_data)
            
            logger.info("Новый токен доступа успешно получен и сохранен в кэш")
            return result['access_token']
        else:
            logger.error(f"Ошибка получения токена: {result.get('error_description', 'Неизвестная ошибка')}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        return None

def get_calendar_events():
    """Получение событий календаря"""
    try:
        access_token = get_access_token()
        if not access_token:
            return []

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        now = datetime.now(UTC)
        # Получаем начало и конец текущего дня
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Форматируем даты в правильном формате для API
        start_time = start_of_day.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"  # Убираем лишние микросекунды
        end_time = end_of_day.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"
        
        # Используем правильный формат URL
        url = f'https://graph.microsoft.com/v1.0/users/{USER_ID}/calendarview'
        params = {
            'startdatetime': start_time,
            'enddatetime': end_time
        }
        
        logger.debug(f"Запрос к API: {url}")
        logger.debug(f"Параметры запроса: {params}")
        logger.debug(f"Заголовки запроса: {headers}")
        
        response = requests.get(url, headers=headers, params=params)
        logger.debug(f"Статус ответа: {response.status_code}")
        logger.debug(f"Тело ответа: {response.json()}")
        logger.debug(f"Заголовки ответа: {response.headers}")
        
        # Проверяем статус ответа
        if response.status_code != 200:
            error_data = response.json()
            error_message = f"Ошибка API: {error_data.get('error', {}).get('message', 'Неизвестная ошибка')}"
            logger.error(f"Ошибка при запросе событий: {error_message}")
            logger.error(f"Полный ответ API: {error_data}")
            logger.error(f"URL запроса: {response.url}")  # Добавляем полный URL с параметрами
            return []
        
        events = response.json().get('value', [])
        logger.info(f"Получено {len(events)} событий на сегодня")
        return events
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при запросе событий: {e}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении событий календаря: {e}")
        return []

async def check_upcoming_events():
    """Проверка предстоящих событий"""
    try:
        events = get_calendar_events()
        if not events:
            logger.warning("Не удалось получить события календаря")
            return
            
        # Получаем текущее время в UTC
        now = datetime.now(UTC)
        
        # Очищаем старые записи из словаря (старше 1 часа)
        current_time = datetime.now(UTC)
        old_keys = []
        for key, timestamp in sent_notifications.items():
            if (current_time - datetime.fromisoformat(timestamp)).total_seconds() > 3600:  # 1 час
                old_keys.append(key)
        
        for key in old_keys:
            del sent_notifications[key]
        
        # Сохраняем очищенный словарь
        save_notifications(sent_notifications)
        
        for event in events:
            try:
                # Проверяем наличие необходимых полей
                if not event or 'start' not in event or 'dateTime' not in event['start']:
                    logger.warning(f"Пропущено событие из-за отсутствия необходимых полей: {event}")
                    continue
                
                # Преобразуем время начала события в UTC
                start_time_str = event['start']['dateTime']
                if start_time_str.endswith('Z'):
                    # Если время заканчивается на Z, это UTC
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                else:
                    # Если нет Z, добавляем UTC
                    start_time = datetime.fromisoformat(start_time_str + '+00:00')
                
                event_title = event.get('subject', 'Без названия')
                event_id = event.get('id', '')  # Получаем ID события
                
                # Получаем информацию о Teams-встрече
                teams_info = ""
                online_meeting = event.get('onlineMeeting', {})
                if online_meeting and online_meeting.get('joinUrl'):
                    teams_info = f"\n🔗 Ссылка на встречу: {online_meeting['joinUrl']}"
                
                # Получаем информацию о месте проведения
                location_info = ""
                location = event.get('location', {})
                if location and location.get('displayName'):
                    location_info = f"\n📍 Место: {location['displayName']}"
                
                # Получаем список участников
                attendees = []
                if event.get('attendees'):
                    for attendee in event['attendees']:
                        try:
                            email_address = attendee.get('emailAddress', {})
                            status = attendee.get('status', {})
                            
                            if email_address and status:
                                name = email_address.get('name', 'Неизвестный участник')
                                response = status.get('response', 'unknown')
                                
                                if response == 'accepted':
                                    attendees.append(f"✅ {name}")
                                elif response == 'declined':
                                    attendees.append(f"❌ {name}")
                                elif response == 'tentativelyAccepted':
                                    attendees.append(f"⚠️ {name}")
                                else:
                                    attendees.append(f"⏳ {name}")
                        except Exception as e:
                            logger.warning(f"Ошибка при обработке участника: {e}")
                            continue
                
                attendees_info = "\n👥 Участники:\n" + "\n".join(attendees) if attendees else ""
                
                # Проверяем, начинается ли событие через 5 минут
                time_diff = start_time - now
                if time_diff <= timedelta(minutes=5) and time_diff > timedelta(minutes=4):
                    notification_key = f"{event_id}_5min"
                    if notification_key not in sent_notifications:
                        message = (
                            f'🔔 Событие начинается через 5 минут\n'
                            f'📅 Событие: {event_title}'
                            f'{location_info}'
                            f'{teams_info}{attendees_info}'
                        )
                        logger.info(f"Отправка уведомления за 5 минут до события: {event_title}")
                        await send_telegram_message(message)
                        sent_notifications[notification_key] = current_time.isoformat()
                        save_notifications(sent_notifications)
                
                # Проверяем, началось ли событие
                if start_time <= now and start_time + timedelta(minutes=1) > now:
                    notification_key = f"{event_id}_start"
                    if notification_key not in sent_notifications:
                        message = (
                            f'🔔 Событие начинается сейчас\n'
                            f'📅 Событие: {event_title}'
                            f'{location_info}'
                            f'{teams_info}{attendees_info}'
                        )
                        logger.info(f"Отправка уведомления о начале события: {event_title}")
                        await send_telegram_message(message)
                        sent_notifications[notification_key] = current_time.isoformat()
                        save_notifications(sent_notifications)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке события {event.get('subject', 'Неизвестное')}: {e}")
                logger.error(f"Данные события: {event}")
    except Exception as e:
        logger.error(f"Ошибка при проверке предстоящих событий: {e}")

async def main():
    logger.info("Программа запущена и отслеживает события календаря...")
    while True:
        try:
            await check_upcoming_events()
            await asyncio.sleep(30)  # Проверяем каждые 30 секунд
        except Exception as e:
            logger.error(f"Произошла ошибка в основном цикле: {e}")
            await asyncio.sleep(60)  # В случае ошибки ждем минуту перед следующей попыткой

if __name__ == "__main__":
    asyncio.run(main())
