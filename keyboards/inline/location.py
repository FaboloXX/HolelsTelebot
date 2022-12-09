from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def location_buttons(locations: dict) -> InlineKeyboardMarkup:
    """
    Функция, создает клавиатуру с двумя кнопками для выбора языка ввода города.
    :param locations: создает клавиатуру с названиями локаций
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i_location, i_location_id in locations.items():
        keyboard.add(InlineKeyboardButton(text=i_location, callback_data=i_location_id))
    return keyboard
