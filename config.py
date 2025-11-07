import os
from dotenv import load_dotenv

# Безопасная загрузка .env (только если файл существует)
if os.path.exists('.env'):
    load_dotenv()
    print("✅ .env файл загружен")
else:
    print("ℹ️ .env файл не найден, используем переменные окружения")

# Получение токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Проверка что обязательные переменные загружены
if not TELEGRAM_TOKEN:
    raise ValueError(
        "❌ TELEGRAM_TOKEN не найден! "
        "Добавь TELEGRAM_TOKEN в .env файл или переменные окружения"
    )

if not OPENAI_API_KEY:
    raise ValueError(
        "❌ OPENAI_API_KEY не найден! "
        "Добавь OPENAI_API_KEY в .env файл или переменные окружения"
    )

print("✅ Все необходимые переменные загружены")

# Системный промпт для Dota 2 анализа
DOTA_SYSTEM_PROMPT = """
Ты - профессиональный аналитик Dota 2 с многолетним опытом. Проанализируй пики противников и рекоменуй лучших героев для выбранной позиции.

Твоя задача:
1. Проанализировать героев противника и их сильные стороны
2. Найти лучших контрпиков для выбранной позиции
3. Оценить шансы на выигрыш в процентах (реалистично, 60-85%)
4. Дать краткое обоснование для каждого героя
5. Предложить общую стратегию против этой команды

Формат ответа ТОЧНО такой:
🎯 РЕКОМЕНДАЦИИ ДЛЯ ПОЗИЦИИ {position}:

🥇 {Герой 1} - {X}% шанс победы
📊 {Краткое обоснование почему этот герой хорош против этой команды}

🥈 {Герой 2} - {Y}% шанс победы  
📊 {Краткое обоснование}

🥉 {Герой 3} - {Z}% шанс победы
📊 {Краткое обоснование}

💡 СТРАТЕГИЯ: {Общий стратегический совет против этой команды}

ВАЖНЫЕ ПРАВИЛА:
- Указывай только номер позиции, например "ПОЗИЦИИ 1"
- Проценты должны быть реалистичными (60-85%)
- Обоснования должны быть краткими и конкретными
- Фокусируйся на контрпиках конкретных героев противника
- Учитывай синергию внутри вражеской команды
- Предлагай практические советы по игре
"""

# Настройки OpenAI
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000,
    "timeout": 30
}

# Настройки бота
BOT_CONFIG = {
    "max_heroes_selection": 5,
    "min_heroes_selection": 1,
    "analysis_timeout": 25,
    "retry_attempts": 3
}

# Логирование
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}


# Проверка конфигурации при импорте
def check_config():
    """Проверка корректности конфигурации"""
    required_vars = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'OPENAI_API_KEY': OPENAI_API_KEY
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            raise ValueError(f"❌ {var_name} не настроен!")

    print("✅ Конфигурация проверена успешно")
    return True


# Автоматическая проверка при импорте
if __name__ != "__main__":
    check_config()

if __name__ == "__main__":
    # Тестирование конфигурации
    print("🔧 Тестирование конфигурации...")
    try:
        check_config()
        print("✅ Все проверки пройдены!")
        print(f"🤖 Telegram Token: {'✅' if TELEGRAM_TOKEN else '❌'}")
        print(f"🧠 OpenAI Key: {'✅' if OPENAI_API_KEY else '❌'}")
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")