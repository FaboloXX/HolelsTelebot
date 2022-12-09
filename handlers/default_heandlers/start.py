from telebot.types import Message
from loader import bot


@bot.message_handler(commands=['start'])
def bot_start(message: Message) -> None:
    """
    Хендлер, ловит команду старт, выдает пользователю приветствие и помогает начать общение.
    :param message: сообщение пользователя
    """
    bot.reply_to(message, f"Привет, {message.from_user.full_name}!\n" +
                 "Я бот для помощи подбора отелей.\n" +
                 "Для вывода доступных команд введите /help"
                 )
