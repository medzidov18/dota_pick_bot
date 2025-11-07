import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, URLInputFile

# Импорты конфигурации и модулей
from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from states import PickStates
from keyboards import (
    get_position_keyboard,
    get_all_heroes_keyboard,
    get_new_analysis_keyboard
)
from dota_analyzer import DotaAnalyzer
from hero_data import POSITION_NAMES, get_clean_hero_name, get_hero_photo_url

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Инициализация анализатора
analyzer = DotaAnalyzer()


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start - выбор позиции"""
    await state.clear()

    welcome_text = """
🎮 <b>Dota 2 Pick Advisor</b>

Я помогу тебе выбрать идеального героя против вражеской команды!

<b>Как это работает:</b>
1. 🎯 Выбери свою позицию (1-5)
2. ⚔️ Выбери героев противника (1-5 героев)  
3. 📊 Получи ТОП-3 рекомендации с шансами на победу!

Выбери свою позицию:
    """

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_position_keyboard()
    )


@dp.callback_query(F.data.startswith("position_"))
async def process_position(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора позиции"""
    position = callback.data.split("_")[1]
    position_name = POSITION_NAMES.get(position, f"Позиция {position}")

    await state.update_data(position=position, selected_heroes=[])
    await state.set_state(PickStates.waiting_enemies)

    selection_text = (
        f"🎯 <b>Твоя позиция:</b> {position_name}\n\n"
        "⚔️ <b>Выбери героев противника:</b> (1-5 героев)\n"
        "Нажимай на героев чтобы выбрать/убрать\n\n"
        f"✅ <b>Выбрано:</b> 0/5 героев"
    )

    await callback.message.edit_text(
        selection_text,
        parse_mode="HTML",
        reply_markup=get_all_heroes_keyboard([])
    )

    await callback.answer(f"Выбрана {position_name}")


@dp.callback_query(F.data.startswith("hero_"), PickStates.waiting_enemies)
async def process_hero_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора героя противника"""
    hero_clean_name = callback.data.split("_", 1)[1]
    user_data = await state.get_data()
    selected_heroes = user_data.get("selected_heroes", [])
    position = user_data.get("position")

    position_name = POSITION_NAMES.get(position, f"Позиция {position}")

    # Добавляем или убираем героя
    if hero_clean_name in selected_heroes:
        selected_heroes.remove(hero_clean_name)
        action = "удален"
    else:
        if len(selected_heroes) < 5:
            selected_heroes.append(hero_clean_name)
            action = "добавлен"
        else:
            await callback.answer("❌ Можно выбрать максимум 5 героев!", show_alert=True)
            return

    await state.update_data(selected_heroes=selected_heroes)

    # Обновляем текст сообщения
    selection_text = (
        f"🎯 <b>Твоя позиция:</b> {position_name}\n\n"
        "⚔️ <b>Выбери героев противника:</b> (1-5 героев)\n"
        "Нажимай на героев чтобы выбрать/убрать\n\n"
        f"✅ <b>Выбрано:</b> {len(selected_heroes)}/5 героев"
    )

    if selected_heroes:
        selection_text += f"\n📋 <b>Список:</b> {', '.join(selected_heroes)}"

    # Обновляем клавиатуру
    await callback.message.edit_text(
        selection_text,
        parse_mode="HTML",
        reply_markup=get_all_heroes_keyboard(selected_heroes)
    )

    await callback.answer(f"{hero_clean_name} {action}")


@dp.callback_query(F.data == "reset_heroes", PickStates.waiting_enemies)
async def reset_heroes(callback: CallbackQuery, state: FSMContext):
    """Сброс выбранных героев"""
    user_data = await state.get_data()
    position = user_data.get("position")
    position_name = POSITION_NAMES.get(position, f"Позиция {position}")

    await state.update_data(selected_heroes=[])

    selection_text = (
        f"🎯 <b>Твоя позиция:</b> {position_name}\n\n"
        "⚔️ <b>Выбери героев противника:</b> (1-5 героев)\n"
        "Нажимай на героев чтобы выбрать/убрать\n\n"
        f"✅ <b>Выбрано:</b> 0/5 героев"
    )

    await callback.message.edit_text(
        selection_text,
        parse_mode="HTML",
        reply_markup=get_all_heroes_keyboard([])
    )

    await callback.answer("Выбор сброшен!")


@dp.callback_query(F.data == "finish_pick", PickStates.waiting_enemies)
async def finish_pick(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора и анализ"""
    user_data = await state.get_data()
    position = user_data.get("position")
    selected_heroes = user_data.get("selected_heroes", [])

    if not selected_heroes:
        await callback.answer("❌ Выбери хотя бы одного героя!", show_alert=True)
        return

    position_name = POSITION_NAMES.get(position, f"Позиция {position}")

    # Показываем индикатор анализа
    analysis_text = (
        f"🔮 <b>Анализирую пики...</b>\n\n"
        f"<b>Твоя позиция:</b> {position_name}\n"
        f"<b>Герои противника:</b> {', '.join(selected_heroes)}\n\n"
        "ИИ подбирает лучшие контрпики..."
    )

    await callback.message.edit_text(
        analysis_text,
        parse_mode="HTML"
    )

    try:
        # Получаем рекомендации от ИИ
        analysis_result = await analyzer.analyze_pick(position, selected_heroes)

        # Извлекаем рекомендованных героев из ответа ИИ
        recommended_heroes = extract_heroes_from_recommendation(analysis_result)

        # Отправляем фото рекомендованных героев
        if recommended_heroes:
            photos_message = "🎯 <b>Рекомендуемые герои:</b>\n"
            await callback.message.answer(photos_message, parse_mode="HTML")

            for hero in recommended_heroes[:3]:  # Максимум 3 героя
                photo_url = get_hero_photo_url(hero)
                if photo_url:
                    try:
                        await callback.message.answer_photo(
                            photo=URLInputFile(photo_url),
                            caption=f"<b>{hero}</b>",
                            parse_mode="HTML"
                        )
                        await asyncio.sleep(0.3)  # Небольшая задержка
                    except Exception as e:
                        logger.error(f"Ошибка отправки фото для {hero}: {e}")
                        # Если фото не отправилось, просто пишем имя героя
                        await callback.message.answer(f"📸 {hero}")

        # Отправляем текстовый анализ
        await callback.message.answer(
            analysis_result,
            parse_mode="Markdown",
            reply_markup=get_new_analysis_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при анализе. Попробуйте еще раз.",
            reply_markup=get_new_analysis_keyboard()
        )

    await state.clear()
    await callback.answer()


def extract_heroes_from_recommendation(text: str) -> list:
    """Извлекает имена героев из рекомендации ИИ"""
    heroes = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        # Ищем строки с медалями
        if '🥇' in line or '🥈' in line or '🥉' in line:
            # Убираем эмодзи и проценты, оставляем только имя героя
            clean_line = line.replace('🥇', '').replace('🥈', '').replace('🥉', '').strip()
            # Убираем проценты и всё после дефиса
            if ' - ' in clean_line:
                hero_part = clean_line.split(' - ')[0].strip()
                # Убираем возможные лишние символы
                hero_part = hero_part.replace('**', '').replace('__', '')
                if hero_part and hero_part not in heroes:
                    heroes.append(hero_part)
            else:
                clean_line = clean_line.replace('**', '').replace('__', '')
                if clean_line and clean_line not in heroes:
                    heroes.append(clean_line)

    # Если не нашли героев в формате, возвращаем популярных по умолчанию
    if not heroes:
        default_heroes = {
            "1": ["Juggernaut", "Phantom Assassin", "Anti-Mage"],
            "2": ["Queen of Pain", "Invoker", "Storm Spirit"],
            "3": ["Axe", "Legion Commander", "Timbersaw"],
            "4": ["Crystal Maiden", "Rubick", "Lion"],
            "5": ["Earthshaker", "Ogre Magi", "Winter Wyvern"]
        }
        return default_heroes.get(position, ["Axe", "Juggernaut", "Crystal Maiden"])

    return heroes


@dp.callback_query(F.data == "new_analysis")
async def new_analysis(callback: CallbackQuery, state: FSMContext):
    """Новый анализ"""
    await cmd_start(callback.message, state)
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда помощи"""
    help_text = """
🤖 <b>Dota 2 Pick Advisor - Помощь</b>

<b>Команды:</b>
/start - Начать подбор героя
/help - Показать эту справку

<b>Как использовать:</b>
1. Нажми /start
2. Выбери свою позицию (1-5)
3. Выбери от 1 до 5 героев противника
4. Получи рекомендации от ИИ

<b>Особенности:</b>
• ИИ анализирует контрпики и синергии
• Показывает шансы на победу в процентах
• Рекомендует 3 лучших героя для твоей позиции

Удачи в игре! 🎮
    """
    await message.answer(help_text, parse_mode="HTML")


@dp.message()
async def handle_other_messages(message: Message):
    """Обработка всех остальных сообщений"""
    await message.answer(
        "🤖 Используй /start чтобы начать подбор героя!\n"
        "Или /help для получения справки."
    )


async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запуск Dota 2 Pick Advisor Bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())