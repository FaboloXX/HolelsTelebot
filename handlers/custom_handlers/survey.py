from loader import bot
from keyboards.reply.photo import request_photo
from keyboards.reply.language import request_language
from keyboards.inline.location import location_buttons
from states.dialog_information import InfoState
from telebot.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from parsers.parser import request_locations, request_hotels, request_hotel_photo
from parsers.api_info import url_locations, url_hotels, url_hotel_photo, headers
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, datetime, timedelta
from database.base import add_data, get_data
from telebot.apihelper import ApiTelegramException


@bot.message_handler(commands=['cancel'])
def bot_start(message: Message) -> None:
    """
    Хендлер, ловит команду cansel, для сброса машины состояний.
    :param message: сообщение пользователя
    """
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.reply_to(message, "Введенные вами данные сброшены.\nВведите команду.")


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def start(message: Message) -> None:
    """
    Хендлер, ловит команду lowprice и бот начинает опрашивать пользователя для формирования запроса.
    Запрашивает язык ввода города и переходит к следующему состоянию.
    :param message: сообщение пользователя
    """
    bot.set_state(message.from_user.id, InfoState.language, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text[1:]
        data['date_time'] = datetime.today().replace(microsecond=0)
    bot.send_message(message.from_user.id,
                     f"Привет {message.from_user.full_name}, выберите язык ввода города",
                     reply_markup=request_language()
                     )


@bot.message_handler(commands=['history'])
def get_history(message: Message) -> None:
    """
    Хендлер, ловит команду history и бот показывает историю поиска отелей пользователем.
    :param message: сообщение пользователя
    """
    data = get_data(message.from_user.id)
    if data:
        date_time = data[0][1]
        hotels = []
        for i in range(len(data)):
            if data[i][1] == date_time:
                # num = len(hotels) + 1
                hotels.append('🔸 ' + data[i][3])
            elif data[i][1] != date_time or i == len(data) - 1:
                date_time = data[i][1]
                n = '\n'
                text = f"📅Дата и время: {data[i][1]}\n" \
                       f"⌨Команда: {data[i][0]}\n" \
                       f"📍Локация: {data[i][2]}\n" \
                       f"🛎Предложенные отели:\n{n.join(hotels)}\n"
                bot.send_message(message.from_user.id, text)
                hotels = []
    else:
        bot.send_message(message.from_user.id, 'Вы еще не пользовались нашими услугами или мы не смогли предложить Вам '
                                               'подходящий отель')


@bot.message_handler(state=InfoState.language)
def get_language(message: Message) -> None:
    """
    Хендлер, ловит сообщение пользователя, запрашивает название города и переходит к следующему состоянию.
    :param message: сообщение пользователя
    """
    if message.text in ('русский', 'английский'):
        bot.set_state(message.from_user.id, InfoState.city, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Понял. Теперь введите название города', reply_markup=ReplyKeyboardRemove())
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if message.text == 'английский':
                data['language'] = 'en_EN'
            elif message.text == 'русский':
                data['language'] = 'ru_RU'
    else:
        bot.send_message(message.from_user.id, 'Чтобы выбрать язык необходимо нажать на соответствующую кнопку')


@bot.message_handler(state=InfoState.city)
def get_city(message: Message) -> None:
    """
    Хендлер, ловит сообщение пользователя, отправляет пользователю инлайн-кнопки, сформированную на данных,
     полученных от сервиса, для уточнения выбранной локации.
    :param message: сообщение пользователя
    """
    querystring = dict()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        querystring['query'] = message.text
        querystring['locale'] = data['language']
    locations = request_locations(url_locations, headers, querystring)
    if locations and len(locations) > 0:
        if len(locations) > 0:
            bot.send_message(message.from_user.id,
                             'Спасибо, записал. Уточните локацию',
                             reply_markup=location_buttons(locations)
                             )
        else:
            bot.send_message(message.from_user.id, 'Такого города не найдено. Попробуйте ввести название еще раз.')
    else:
        bot.send_message(message.from_user.id, 'Извините, проблемы на сервере, попробуйте позже')



@bot.callback_query_handler(func=lambda call: call.data.startswith('city_id:'))
def callback_inline(call: CallbackQuery) -> None:
    """
    Хендлер, ловит нажатие инлайн-кнопки пользователем, формирует инлайн-кнопки для выбора даты заезда.
    :param call: запрос обратной связи от инлайн-кнопки с заданным callback_data.
    """
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['id_location'] = call.data.split(':')[1]
    bot.answer_callback_query(call.id)
    bot.set_state(call.from_user.id, InfoState.arrival_date, call.message.chat.id)
    calendar = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=date.today()).build()
    bot.send_message(call.message.chat.id,
                     'Выберите дату заезда',
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def call_func(call: CallbackQuery) -> None:
    """
    Хендлер, ловит выбор даты заезда пользователем, формирует инлайн-кнопки для выбора даты выезда.
    :param call: запрос обратной связи от инлайн-кнопки с заданным callback_data.
    """
    result, key, step = DetailedTelegramCalendar(calendar_id=1,
                                                 locale='ru',
                                                 min_date=date.today()).process(call.data)
    if not result and key:
        bot.edit_message_text('Выберите дату заезда',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Дата заезда {result}",
                              call.message.chat.id,
                              call.message.message_id)
        bot.set_state(call.from_user.id, InfoState.departure_date, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['arrival_date'] = result
            calendar = DetailedTelegramCalendar(calendar_id=2,
                                                locale='ru',
                                                min_date=data['arrival_date'] + timedelta(days=1)
                                                ).build()
        bot.send_message(call.message.chat.id,
                         'Выберите дату выезда',
                         reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def call_func(call: CallbackQuery) -> None:
    """
    Хендлер, ловит выбор даты выезда пользователем, запрашивает у пользователя количество отелей
    или минимальную цену за ночь.
    :param call: запрос обратной связи от инлайн-кнопки с заданным callback_data.
    """
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        result, key, step = DetailedTelegramCalendar(calendar_id=2,
                                                     locale='ru',
                                                     min_date=data['arrival_date'] + timedelta(days=1)
                                                     ).process(call.data)
    if not result and key:
        bot.edit_message_text('Выберите дату выезда',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.set_state(call.from_user.id, InfoState.hotel_count, call.message.chat.id)
        bot.edit_message_text(f"Дата выезда {result}",
                              call.message.chat.id,
                              call.message.message_id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['departure_date'] = result
            delta = data['departure_date'] - data['arrival_date']
            data['days'] = delta.days
            if data['command'] == 'lowprice' or data['command'] == 'highprice':
                bot.set_state(call.from_user.id, InfoState.hotel_count, call.message.chat.id)
                bot.send_message(call.message.chat.id, 'Какое количество отелей вывести(не более 10)?')
            elif data['command'] == 'bestdeal':
                bot.set_state(call.from_user.id, InfoState.min_price, call.message.chat.id)
                bot.send_message(call.message.chat.id, 'Введите минимальную цену за ночь')


@bot.message_handler(state=InfoState.min_price)
def get_hotel_count(message: Message) -> None:
    """
    Хендлер, ловит минимальную цену за ночь, запрашивает у пользователя максимальную цену за ночь.
    :param message: сообщение пользователя
    """
    if message.text.isdigit():
        bot.send_message(message.from_user.id,
                         'Спасибо, записал. Введите максимальную цену за ночь')
        bot.set_state(message.from_user.id, InfoState.max_price, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_price'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Нужно использовать цифры')


@bot.message_handler(state=InfoState.max_price)
def get_hotel_count(message: Message) -> None:
    """
    Хендлер, ловит максимальную цену за ночь, запрашивает у пользователя количество отелей
    либо максимальное расстояние до центра.
    :param message: сообщение пользователя
    """
    if message.text.isdigit():
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_price'] = message.text
            if data['command'] == 'bestdeal':
                bot.set_state(message.from_user.id, InfoState.distance, message.chat.id)
                bot.send_message(message.from_user.id,
                                 'Спасибо, записал.\nКакое максимальное расстояние от центра в км Вас устроит?')
            else:
                bot.set_state(message.from_user.id, InfoState.hotel_count, message.chat.id)
                bot.send_message(message.from_user.id,
                                 'Спасибо, записал.\nКакое количество отелей вывести(не более 10)?')
    else:
        bot.send_message(message.from_user.id, 'Нужно использовать цифры')


@bot.message_handler(state=InfoState.distance)
def get_hotel_count(message: Message) -> None:
    """
    Хендлер, ловит максимальное расстояние до центра, запрашивает у пользователя количество отелей
    :param message: сообщение пользователя
    """
    if message.text.isdigit():
        bot.set_state(message.from_user.id, InfoState.hotel_count, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Спасибо, записал.\nКакое количество отелей вывести(не более 10)?')
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['distance'] = message.text
    else:
        bot.send_message(message.from_user.id, 'Нужно использовать цифры')


@bot.message_handler(state=InfoState.hotel_count)
def get_hotel_count(message: Message) -> None:
    """
    Хендлер, ловит количество отелей, запрашивает у пользователя необходимость загрузки фотографий.
    :param message: сообщение пользователя
    """
    if message.text.isdigit():
        if 10 >= int(message.text) >= 1:
            bot.send_message(message.from_user.id,
                             'Спасибо, записал. Нужны ли Вам фото? Нажмите кнопку "Да" или "Нет"',
                             reply_markup=request_photo())
            bot.set_state(message.from_user.id, InfoState.photo, message.chat.id)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['hotel_count'] = message.text
        else:
            bot.send_message(message.from_user.id, 'Количество отелей не может быть меньше чем 1 и больше чем 10')
    else:
        bot.send_message(message.from_user.id, 'Нужно использовать цифры')


@bot.message_handler(state=InfoState.photo)
def get_photo(message: Message) -> None:
    """
    Хендлер, ловит необходимость загрузки фотографий, при положительном ответе запрашивает их количество.
    :param message: сообщение пользователя
    """
    if message.text == 'Да':
        bot.send_message(message.from_user.id,
                         'Теперь введите, сколько фото вам будет достаточно, но не больше 5',
                         reply_markup=ReplyKeyboardRemove()
                         )
        bot.set_state(message.from_user.id, InfoState.photo_count, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['hotel_photo'] = message.text
    elif message.text == 'Нет':
        bot.send_message(message.from_user.id, 'Спасибо, записал')
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['hotel_photo'] = None
            data['photo_count'] = None
        get_result(message)
    else:
        bot.send_message(message.from_user.id, 'Необходимо нажать кнопку "Да" или "Нет"')


@bot.message_handler(state=InfoState.photo_count)
def get_photo_count(message: Message) -> None:
    """
    Хендлер, ловит количество фотографий, вызывает функцию для вывода результата запроса.
    :param message: сообщение пользователя
    """
    if message.text.isdigit():
        if 0 < int(message.text) <= 5:
            bot.send_message(message.from_user.id, 'Спасибо, записал')
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['photo_count'] = int(message.text)
            get_result(message)
        else:
            bot.send_message(message.from_user.id, 'Количество фото должно быть больше 0 и не больше 10')
    else:
        bot.send_message(message.from_user.id, 'Необходимо ввести число')


def get_result(message: Message) -> None:
    """
    Функция, отправляет результаты запроса в чат с пользователем, сбрасывает машину состояний.
    :param message: сообщение пользователя
    """
    bot.send_message(message.from_user.id, 'Минуточку, подбираю варианты...')
    text_not_found = 'Извините, но по вашим требованиям вариантов не найдено.\n' \
                     'Попробуйте снова и поменяйте критерия поиска'
    text_server_problem = 'Извините, у нас проблемы на сервере.\n' \
                          'Попробуйте позже.'
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if data['command'] == 'lowprice':
            querystring_hotel = {"destinationId": data['id_location'],
                                 "pageNumber": '1',
                                 "pageSize": data['hotel_count'],
                                 "checkIn": data['arrival_date'],
                                 "checkOut": data['departure_date'],
                                 "adults1": "1",
                                 "sortOrder": 'PRICE',
                                 "locale": 'ru_RU',
                                 "currency": 'RUB'}
        elif data['command'] == 'highprice':
            querystring_hotel = {"destinationId": data['id_location'],
                                 "pageNumber": '1',
                                 "pageSize": data['hotel_count'],
                                 "checkIn": data['arrival_date'],
                                 "checkOut": data['departure_date'],
                                 "adults1": "1",
                                 "sortOrder": 'PRICE_HIGHEST_FIRST',
                                 "locale": 'ru_RU',
                                 "currency": 'RUB'}
        elif data['command'] == 'bestdeal':
            querystring_hotel = {"destinationId": data['id_location'],
                                 "pageNumber": '1',
                                 "pageSize": '25',
                                 "checkIn": data['arrival_date'],
                                 "checkOut": data['departure_date'],
                                 "adults1": "1",
                                 "locale": 'ru_RU',
                                 "currency": 'RUB',
                                 "sortOrder": 'DISTANCE_FROM_LANDMARK',
                                 "priceMin": data['min_price'],
                                 "priceMax": data['max_price']
                                 }
        else:
            querystring_hotel = None
        days = data['days']
        photo_count = data['photo_count']
        hotels = request_hotels(url_hotels, headers, querystring_hotel, days)
    if not bool(hotels):
        bot.send_message(message.from_user.id, text_not_found)
    elif hotels is None:
        bot.send_message(message.from_user.id, text_server_problem)
    else:
        name_hotels = list()
        data['location'] = hotels[0]['location']
        if data['command'] == 'bestdeal':
            count = 0
            for i_hotel in hotels:
                count += 1
                if float(i_hotel['distance'][:-3].replace(',', '.')) <= int(data['distance']):
                    text = f"🛎Отель: {i_hotel['name']}\n" \
                           f"🏆Рейтинг: {i_hotel['rating']}\n" \
                           f"📍Адрес: {i_hotel['address']}\n" \
                           f"🚕До центра: {i_hotel['distance']}\n" \
                           f"💴Цена за ночь: {i_hotel['price']}\n" \
                           f"💰Общая стоимость: {i_hotel['total_price']}\n" \
                           f"🌐Сайт: {i_hotel['web_site']}"
                    name_hotels.append(i_hotel['name'])
                else:
                    text = None
                if photo_count:
                    send_message_with_photo(message, text, photo_count, i_hotel)
                elif not photo_count and bool(name_hotels) is True:
                    bot.send_message(message.from_user.id, text, disable_web_page_preview=True)
                if count == int(data['hotel_count']):
                    break
            if not bool(name_hotels):
                bot.send_message(message.from_user.id, text_not_found)
        else:
            for i_hotel in hotels:
                text = f"🛎Отель: {i_hotel['name']}\n" \
                       f"🏆Рейтинг: {i_hotel['rating']}\n" \
                       f"📍Адрес: {i_hotel['address']}\n" \
                       f"🚕До центра: {i_hotel['distance']}\n" \
                       f"💴Цена за ночь: {i_hotel['price']}\n" \
                       f"💰Общая стоимость: {i_hotel['total_price']}\n" \
                       f"🌐Сайт: {i_hotel['web_site']}"
                name_hotels.append(i_hotel['name'])
                if photo_count:
                    send_message_with_photo(message, text, photo_count, i_hotel)
                else:
                    bot.send_message(message.from_user.id, text, disable_web_page_preview=True)

        if bool(name_hotels):
            add_data(data['command'], data['date_time'], data['location'], message.from_user.id, name_hotels)
    bot.delete_state(message.from_user.id, message.chat.id)


def send_message_with_photo(message: Message, text: str, photo_count: int, hotel: dict) -> None:
    """
    Функция, котора формирует сообщение пользователю если он запросил фото отелей.
    :param message: сообщение пользователя
    :param text: текст с описанием отеля
    :param photo_count: количество фото отеля
    :param hotel: словарь с информацией по отелю
    """
    photos = request_hotel_photo(url_hotel_photo, headers, photo_count, querystring={'id': hotel['id']})
    if not bool(photos):
        bot.send_message(message.from_user.id, 'Фотографии не найдены\n' + text)
    else:
        if photo_count == 1:
            try:
                bot.send_photo(message.from_user.id, photo=photos[0], caption=text)
            except ApiTelegramException:
                bot.send_message(message.from_user.id, 'Фотографии не найдены\n' + text)
        else:
            media = list()
            for i_photo in photos:
                if photos.index(i_photo) == 0:
                    try:
                        media.append(InputMediaPhoto(media=i_photo, caption=text))
                    except ApiTelegramException:
                        bot.send_message(message.from_user.id, 'Фотографии не найдены\n' + text)
                else:
                    media.append(InputMediaPhoto(i_photo))
            try:
                bot.send_media_group(message.from_user.id, media=media)
            except ApiTelegramException:
                bot.send_message(message.from_user.id, 'Фотографии не найдены\n' + text)
