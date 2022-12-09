import sqlite3 as sq
from datetime import datetime


def start_sq() -> None:
    """
    Функция, подключает базу данных, создает необходимые таблицы, если они не были созданы ранее.
    """
    base = sq.connect('database/history.db')
    if base:
        print('Data base is connected!')
    base.execute('CREATE TABLE IF NOT EXISTS commands '
                 '(id integer PRIMARY KEY AUTOINCREMENT NOT NULL, '
                 'name,'
                 'date_time,'
                 'location,'
                 'user_id)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS hotels (id integer PRIMARY KEY AUTOINCREMENT NOT NULL, name, id_commands)')
    base.commit()


def add_data(command: str, date_time: datetime, location: str, user_id: int, hotels: list) -> None:
    """
    Функция, добавляет в базу данных историю поиска пользователем отелей.
    :param command: команда пользователя по поиску отеля
    :param date_time: дата и время вызова команды
    :param location: локация в которой производился поиск отелей
    :param user_id: id пользователя телеграмм
    :param hotels: список названий отелей которые были найдены
    """
    base = sq.connect('database/history.db')
    cur = base.cursor()
    cur.execute('INSERT INTO commands (name, date_time, location, user_id) VALUES(?, ?, ?, ?)',
                (command, date_time, location, user_id))
    base.commit()
    history_id = cur.execute('SELECT id FROM commands ORDER BY id DESC LIMIT 1').fetchone()
    for i_hotel in hotels:
        cur.execute('INSERT INTO hotels (name, id_commands) VALUES(?, ?)',
                    (i_hotel, history_id[0]))
    base.commit()


def get_data(user_id: int) -> list:
    """
    Функция, предоставляет историю поиска отелей из базы данных.
    :param user_id: id пользователя телеграмм
    """
    base = sq.connect('database/history.db')
    cur = base.cursor()
    query = cur.execute('SELECT c.name, c.date_time, c.location, h.name '
                        'FROM commands c JOIN hotels h ON c.id == h.id_commands '
                        'WHERE c.user_id = ?', (user_id,)).fetchall()
    return query
