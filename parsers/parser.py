import requests
import json
import re
from typing import Optional, Union, Any


def request_to_api(url: str, headers: dict, querystring: dict) -> requests.Response:
    """
    Функция, проверяет что приходит с сервера на запрос. При положительном ответе, возвращает результат запроса.
    :param url: адрес запроса,
    :param headers: заголовки, для получения информации с rapid.api,
    :param querystring: параметры, необходимые для формирования запроса
    :return: requests.Response - объект ответа сервера
    """
    try:
        response = requests.get(url=url, headers=headers, params=querystring, timeout=30)
        if response.status_code == requests.codes.ok:
            return response
    except Exception as exc:
        print(f'Ошибка: {exc}')


def request_locations(url: str, headers: dict, querystring: dict) -> Optional[dict[str, Union[str, Any]]]:
    """
    Функция, запрашивает у rapid.api список локаций, формирует в словарь
    :param url: адрес запроса
    :param headers: заголовки, для получения информации с rapid.api
    :param querystring: параметры, необходимые для формирования запроса
    :return: cловарь с названиями локаций и их id
    """
    pattern = r'(?<="CITY_GROUP",).+?[\]]'
    request = request_to_api(url, headers, querystring)
    if request is None:
        return
    else:
        find = re.search(pattern,  request.text)
        if find:
            result = json.loads(f"{{{find[0]}}}")
            locations = dict()
            for i_pos in range(len(result['entities'])):
                data = result['entities'][i_pos]['caption']
                location = re.sub(r'(<(/?[^>]+)>)', '', data)
                locations[location] = 'city_id:' + result['entities'][i_pos]['destinationId']
        else:
            locations = dict()
        return locations


def request_hotels(url: str, headers: dict, querystring: dict, days: int) -> Optional[list[dict[str, Union[str, Any]]]]:
    """
    Функция, запрашивает у rapid.api список отелей по выбранной локации,
    :param url: адрес запроса
    :param headers: заголовки, для получения информации с rapid.api
    :param querystring: параметры, необходимые для формирования запроса
    :param days: количество суток пребывания в отеле
    :return: список словарей с данными по отелям
    """
    pattern = r'(?<=,)"results":.+?(?=,"pagination)'
    request = request_to_api(url, headers, querystring)
    if request is None:
        return
    else:
        data = request.text
        find = re.search(pattern, data)

        if find:
            result = json.loads(f"{{{find[0]}}}")
            j_data = json.loads(data)
            hotel_list = list()
            for i_pos in range(len(result['results'])):
                hotel_dict = dict()
                hotel_dict['location'] = j_data['data']['body']['header']
                hotel_dict['name'] = result['results'][i_pos]['name']
                hotel_dict['id'] = result['results'][i_pos]['id']
                hotel_dict['web_site'] = 'hotels.com/ho' + str(hotel_dict['id'])
                hotel_dict['star'] = result['results'][i_pos]['starRating']
                try:
                    hotel_dict['rating'] = result['results'][i_pos]['guestReviews']['unformattedRating']
                except KeyError:
                    hotel_dict['rating'] = 'нет данных'
                try:
                    address = ''
                    for i_key, i_value in result['results'][i_pos]['address'].items():
                        if i_key == 'region':
                            break
                        elif i_value != '':
                            address += i_value + ', '
                    hotel_dict['address'] = address[:-2]
                except KeyError:
                    hotel_dict['address'] = 'нет данных'
                hotel_dict['distance'] = result['results'][i_pos]['landmarks'][0]['distance']
                hotel_dict['price'] = result['results'][i_pos]['ratePlan']['price']['current']
                hotel_dict['total_price'] = "{:,.0f} RUB".format(days * result['results'][i_pos]['ratePlan']['price']['exactCurrent'])
                hotel_list.append(hotel_dict)
        else:
            hotel_list = []
        return hotel_list


def request_hotel_photo(url: str, headers: dict, count: int, querystring: dict) -> list:
    """
    Функция, запрашивает у rapid.api список фото отелей
    :param url: адрес запроса
    :param headers: заголовки, для получения информации с rapid.api
    :param querystring: параметры, необходимые для формирования запроса
    :param count: количество фото отеля
    :return: список c со ссылками на фото отелей
    """
    pattern = r'(https.*?){'
    find = re.findall(pattern, request_to_api(url, headers, querystring).text)
    photo_list = []
    if find:
        for i in range(count):
            photo_list.append(find[i] + 'z.jpg')
    else:
        photo_list = []
    return photo_list

