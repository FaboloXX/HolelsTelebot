from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def request_language() -> ReplyKeyboardMarkup:
    """
    Функция, создает клавиатуру с двумя кнопками для выбора языка ввода города.
    """
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton('русский'), KeyboardButton('английский'))
    return keyboard
