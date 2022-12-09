from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def request_photo() -> ReplyKeyboardMarkup:
    """
    Функция, создает клавиатуру с двумя кнопками для ответа на необходимость загрузки фото отелей.
    """
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    return keyboard
