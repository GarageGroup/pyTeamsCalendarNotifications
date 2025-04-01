# Уведомления о встречах Teams в Telegram

Это приложение автоматически отслеживает встречи в календаре Microsoft Teams и отправляет уведомления о них через Telegram. Оно помогает не пропустить важные встречи и всегда иметь под рукой ссылки на них.

## Основные возможности

- Автоматическое отслеживание встреч в календаре Teams
- Отправка уведомлений в Telegram с информацией о встрече:
  - Название встречи
  - Время начала
  - Ссылка на встречу в Teams
  - Место проведения (если указано)
  - Список участников с их статусом участия
- Уведомления отправляются:
  - За 5 минут до начала встречи
  - В момент начала встречи
- Кэширование токена доступа для оптимизации запросов
- Сохранение истории отправленных уведомлений
- Подробное логирование всех операций

## Требования

- Python 3.x
- Учетная запись Microsoft 365
- Telegram бот (получить токен можно у @BotFather)
- Node.js и npm (для развертывания через PM2)

## Установка

1. Клонируйте репозиторий:
```bash
git clone [URL репозитория]
cd pyTeamsCalendarNotifications
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и заполните необходимые переменные окружения:
```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
TENANT_ID=your_tenant_id
USER_ID=your_user_id
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## Настройка

1. Зарегистрируйте приложение в Azure AD:
   - Перейдите в [Azure Portal](https://portal.azure.com)
   - Создайте новое приложение
   - Получите CLIENT_ID и CLIENT_SECRET
   - Настройте необходимые разрешения для Microsoft Graph API

2. Создайте Telegram бота:
   - Найдите @BotFather в Telegram
   - Создайте нового бота
   - Получите токен бота
   - Получите ID чата, куда будут отправляться уведомления

## Структура проекта

```
pyTeamsCalendarNotifications/
├── data/                  # Директория для хранения данных
│   ├── sent_notifications.json  # История отправленных уведомлений
│   └── token_cache.json        # Кэш токена доступа
├── logs/                  # Директория для логов
│   ├── info.log          # Основные логи
│   ├── error.log         # Логи ошибок
│   └── debug.log         # Отладочные логи
├── main.py               # Основной скрипт
├── requirements.txt      # Зависимости проекта
├── ecosystem.config.js   # Конфигурация PM2
└── .env                 # Конфигурация окружения
```

## Логирование

Приложение ведет подробные логи в трех файлах:
- `logs/info.log` - основная информация
- `logs/error.log` - ошибки
- `logs/debug.log` - отладочная информация

## Развертывание на Ubuntu через PM2

1. Установите Node.js и npm:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. Установите PM2 глобально:
```bash
sudo npm install -g pm2
```

3. Настройте виртуальное окружение Python:
```bash
# Установите python3-venv если еще не установлен
sudo apt-get install python3-venv

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Убедитесь, что все зависимости установлены корректно
pip list
```

4. Запустите приложение через PM2:
```bash
# Убедитесь, что вы находитесь в директории проекта
cd /path/to/pyTeamsCalendarNotifications

# Запустите приложение
pm2 start ecosystem.config.js

# Проверьте логи на наличие ошибок
pm2 logs pyTeamsCalendarNotifications
```

5. Настройте автозапуск PM2 при перезагрузке системы:
```bash
pm2 startup
pm2 save
```

6. Полезные команды PM2:
```bash
pm2 status              # Проверка статуса приложения
pm2 logs pyTeamsCalendarNotifications  # Просмотр логов
pm2 restart pyTeamsCalendarNotifications  # Перезапуск приложения
pm2 stop pyTeamsCalendarNotifications    # Остановка приложения
pm2 delete pyTeamsCalendarNotifications  # Удаление приложения из PM2
```

## Безопасность

- Все чувствительные данные хранятся в переменных окружения
- Используется безопасная аутентификация через Azure AD
- Логи не содержат конфиденциальной информации
- Токены доступа кэшируются и автоматически обновляются
- История уведомлений хранится в отдельной директории

## Лицензия

MIT
