from telebot.handler_backends import State, StatesGroup


class InfoState(StatesGroup):
    arrival_date = State()
    city = State()
    departure_date = State()
    distance = State()
    hotel_count = State()
    language = State()
    location = State()
    max_price = State()
    min_price = State()
    photo = State()
    photo_count = State()
    start = State()

