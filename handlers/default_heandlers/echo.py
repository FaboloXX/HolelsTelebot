from telebot.types import Message
from loader import bot


@bot.message_handler(state=None)
def bot_echo(message: Message):
    """
    Хендлер, ловит любые непонятные боту сообщения при начале работы.
    :param message: сообщение пользователя
    """
    bot.reply_to(message, "Для начала общение введите /start.")
