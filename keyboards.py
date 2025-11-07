from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from hero_data import POSITION_NAMES, POSITION_HEROES, get_clean_hero_name


def get_position_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора позиции"""
    builder = InlineKeyboardBuilder()

    for pos_num, pos_name in POSITION_NAMES.items():
        builder.button(text=pos_name, callback_data=f"position_{pos_num}")

    builder.adjust(1)
    return builder.as_markup()


def get_all_heroes_keyboard(selected_heroes: list = None) -> InlineKeyboardMarkup:
    """Клавиатура со ВСЕМИ героями на одной странице"""
    if selected_heroes is None:
        selected_heroes = []

    builder = InlineKeyboardBuilder()

    # Собираем всех героев из всех позиций
    all_heroes = []
    for heroes in POSITION_HEROES.values():
        all_heroes.extend(heroes)

    # Сортируем героев по алфавиту (по чистому имени)
    all_heroes.sort(key=lambda x: get_clean_hero_name(x))

    # Создаем кнопки для всех героев
    for hero in all_heroes:
        clean_name = get_clean_hero_name(hero)
        is_selected = any(clean_name in selected for selected in selected_heroes)
        emoji = "✅ " if is_selected else ""
        builder.button(
            text=f"{emoji}{hero}",
            callback_data=f"hero_{clean_name}"
        )

    # Кнопки управления
    if selected_heroes:
        builder.button(text="🚀 Получить рекомендации", callback_data="finish_pick")

    builder.button(text="🔄 Сбросить выбор", callback_data="reset_heroes")

    # Настраиваем расположение - 3 колонки для компактности
    builder.adjust(3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2)
    return builder.as_markup()


def get_new_analysis_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после выдачи рекомендаций"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Новый анализ", callback_data="new_analysis")
    builder.adjust(1)
    return builder.as_markup()