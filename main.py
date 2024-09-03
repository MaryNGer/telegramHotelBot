import functools
import os.path
import traceback
from time import sleep
from typing import Callable, Union
import datetime
import telebot
from telebot import types
from telebot import time
import requests
import json
import re
import my_token

from config import history_dct, person_dict, func, activ_func, func_best, activ_func_best

bot = telebot.TeleBot(my_token.token)


def exc_handler(method: Callable) -> Callable:
    """
    Декоратор. Логирует исключение вызванной функции, уведомляет пользователя об ошибке.
    """

    @functools.wraps(method)
    def wrapped(message: Union[types.Message, types.CallbackQuery]) -> None:
        try:
            method(message)
        except ValueError as exception:
            if isinstance(message, types.CallbackQuery):
                message = message.message
            if exception.__class__.__name__ == 'JSONDecodeError':
                exc_handler(method(message))
        except Exception as exception:
            bot.send_message(message.chat.id, 'Что-то пошло не так, перезагружаюсь...')
            with open('errors_log.txt', 'a') as file:
                file.write('\n'.join([datetime.datetime.now(), exception.__class__.__name__, traceback.format_exc(),
                                      '\n\n']))
            sleep(1)
            start(message)

    return wrapped


def markup():
    """
    Создание кнопки 'Назад'
    """
    mark = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Назад")
    mark.add(btn)


@bot.message_handler(regexp=r'.*[Пп]ривет.*')
@bot.message_handler(commands=['start'])
@exc_handler
def start(message):
    """
    Функция start, приветствие пользователя
    """
    markup()
    bot.send_message(message.chat.id, 'Добро пожаловать!')
    help_func(message)


@bot.message_handler(commands=['help'])
@exc_handler
def help_func(message):
    """
    Функция для обработки команды /help в телеграм-боте.
    Отправляет пользователю сообщение с описанием доступных команд бота и активирует флаги для дальнейшей обработки.
    """
    bot.send_message(message.chat.id, "/low_price - Топ самых дешёвых отелей в городе\n"
                                      "/high_price - Топ самых дорогих отелей в городе\n"
                                      "/best_deal  - Топ отелей, наиболее подходящих по цене "
                                      "и расположению от центра"
                                      "(самые дешёвые и находятся ближе всего к центру)\n"
                                      "/history  - История поиска отелей ")
    activ_func[1] = 1
    activ_func_best[1] = 1


@bot.message_handler(commands=['low_price', 'high_price', 'best_deal'])
@exc_handler
def ask_city(message):
    """
    Функция для обработки команд /low_price, /high_price и /best_deal в телеграм-боте.
    Запрашивает у пользователя ввод города, в котором будет производиться поиск отелей,
    сохраняет информацию о команде и времени запроса, а также активирует определенные флаги для дальнейшей обработки.
    Вызывает следующую функцию для обработки сообщения
    """
    tvc = lambda x: time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(x))
    time_mes = tvc(message.date)
    history_dct['func'] = message.text
    history_dct['time'] = time_mes
    person_dict['func'] = message.text
    bot.send_message(message.chat.id, "Введите город:")

    activ_func[2] = 1
    activ_func_best[2] = 1
    bot.register_next_step_handler(message, back)


def back(message):
    """
    Функция для обработки ответа пользователя после запроса ввода города.
    Проверяет, хочет ли пользователь вернуться на предыдущий шаг или продолжить с введенным городом,
    и вызывает соответствующие функции для дальнейшей обработки.
    """
    text = message.text
    count = 0
    if text == "Назад":
        if person_dict['func'] == '/best_deal':
            back_best(message)
        else:
            for x in activ_func.values():
                if x == 1:
                    count += 1
            activ_func[count] = 0
            count -= 1
            if func[count] == search_by_city:
                activ_func[count] = 0
                count -= 1
                func[count](message)
            elif func[count] == check_in_out:
                activ_func[count] = 0
                count -= 1
                func[count](message)
            elif func[count] == count_hotel:
                activ_func[count] = 0
                count -= 1
                func[count](message)
            else:
                func[count](message)
    else:
        if person_dict['func'] == '/best_deal':
            back_best(message)
        else:
            for k, v in activ_func.items():
                if v == 0:
                    func[k](message)
                    break


def back_best(message):
    """
    Функция для обработки ответа пользователя после запроса ввода города при выполнении команды /best_deal.
    Проверяет, хочет ли пользователь вернуться на предыдущий шаг или продолжить с введенным городом,
    и вызывает соответствующие функции для дальнейшей обработки.
    """
    text = message.text
    count = 0
    if text == "Назад":
        for x in activ_func_best.values():
            if x == 1:
                count += 1
        activ_func_best[count] = 0
        count -= 1
        if func_best[count] == search_by_city:
            activ_func_best[count] = 0
            count -= 1
            func_best[count](message)
        elif func_best[count] == range_price:
            activ_func_best[count] = 0
            count -= 1
            func_best[count](message)
        elif func_best[count] == range_distance:
            activ_func_best[count] = 0
            count -= 1
            func_best[count](message)
        elif func_best[count] == check_in_out:
            activ_func_best[count] = 0
            count -= 1
            func_best[count](message)
        elif func_best[count] == count_hotel:
            activ_func_best[count] = 0
            count -= 1
            func_best[count](message)
        else:
            func_best[count](message)
    else:
        for k, v in activ_func_best.items():
            if v == 0:
                func_best[k](message)
                break


@bot.message_handler(commands=['history'])
@exc_handler
def history(message):
    """
    Функция предназначена для обработки команды /history в телеграм-боте.
    Загружает историю поиска отелей из JSON-файла и отправляет пользователю информацию о предыдущих поисковых запросах,
    включая команды, время запросов и результаты поиска (названия отелей и фотографии).
    """
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as file:
            dct = json.load(file)

        if dct.get(str(message.chat.id)):
            for value in dct[str(message.chat.id)]:
                text_func = 'Команда:{func}\nВремя:{time}'.format(func=value['func'], time=value['time'])
                bot.send_message(message.chat.id, text_func, parse_mode='Markdown')
                for hotel, photo in value['result_hotel'].items():

                    if value['result_hotel'][hotel] is None:
                        bot.send_message(message.chat.id, hotel, parse_mode='Markdown')
                    else:
                        result = []
                        for i_photo in photo:
                            if not result:
                                result.append(
                                    types.InputMediaPhoto(caption=hotel, media=i_photo,
                                                          parse_mode='Markdown'))
                            else:
                                result.append(types.InputMediaPhoto(media=i_photo))
                        bot.send_media_group(message.chat.id, media=result)
            bot.send_message(message.chat.id, 'Показ истории завершен\nНачать с начала нажмите /help')
    else:
        bot.send_message(message.chat.id, 'К сожалению истории еще нет\nДавайте ее создадим =)\nНажмите /help')


@bot.message_handler(content_types=['text'])
@exc_handler
def anything(message):
    """
    Функция для обработки текстовых сообщений, которые не соответствуют ни одной из заранее определенных команд.
    Отправляет пользователю сообщение с описанием доступных команд бота и активирует определенные флаги
    для дальнейшей обработки.
    """
    bot.send_message(message.chat.id, "/low_price - Топ самых дешёвых отелей в городе\n"
                                      "/high_price - Топ самых дорогих отелей в городе\n"
                                      "/best_deal  - Топ отелей, наиболее подходящих по цене "
                                      "и расположению от центра"
                                      "(самые дешёвые и находятся ближе всего к центру)\n"
                                      "/history  - История поиска отелей ")

    activ_func[1] = 1
    activ_func_best[1] = 1


def search_by_city(message):
    """
    Функция для проверки в ведённого города
    """
    name = message.text

    activ_func[3] = 1
    activ_func_best[3] = 1

    if re.fullmatch(r'^\D+', name, re.I):
        city_list = get_city_list(message)
        if not city_list:
            bot.send_message(message.chat.id, "Такого города нет. Введите город заново")
            bot.register_next_step_handler(message, search_by_city)
        else:
            keyboard = types.InlineKeyboardMarkup()
            for city_name, city_id in city_list.items():
                keyboard.add(types.InlineKeyboardButton(text=city_name, callback_data=city_id))
            bot.send_message(message.from_user.id, 'Вот что удалось найти\nУточните пожалуйста', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Ошибка, попробуйте еще раз.")
        bot.register_next_step_handler(message, search_by_city)


@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    """
    Функция для обработки callback-запросов (нажатий на кнопки) в телеграм-боте.
    Обрабатывает различные типы callback-данных и вызывает соответствующие функции для дальнейшей обработки.
    """
    if call.data.isdigit():
        person_dict['city_id'] = str(call.data)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Вот что удалось найти\nУточните пожалуйста", reply_markup=None)
        if person_dict['func'] == '/best_deal':
            ask_range_price(call.message)
        else:
            data(call.message)
    if call.data == "yes":
        person_dict['photo'] = True
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Хотите загрузить фотографии для каждого отеля", reply_markup=None)
        ask_count_photo(call.message)
    elif call.data == "no":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Хотите загрузить фотографии для каждого отеля", reply_markup=None)
        total_result(call.message)


def ask_range_price(message):
    """
    Функция для запроса у пользователя диапазона цен на отели при выполнении команды /best_deal.
    Отправляет сообщение с просьбой ввести диапазон цен и регистрирует следующий шаг обработки сообщения.
    """
    activ_func_best[4] = 1
    bot.send_message(message.chat.id, 'Ведите диапазон цен (от-до через -)')
    bot.register_next_step_handler(message, back)


def data(message):
    """
    Функция запроса у пользователя дат заезда и выезда из отеля.
    Отправляет сообщение с просьбой ввести даты в формате "ДД.ММ.ГГГГ - ДД.ММ.ГГГГ"
    и регистрирует следующий шаг обработки сообщения.
    """
    activ_func[4] = 1
    activ_func_best[8] = 1
    bot.send_message(message.chat.id, 'С какого по какое число хотите остановиться?\n'
                                      '(ДД.ММ.ГГГГ - ДД.ММ.ГГГГ)')
    bot.register_next_step_handler(message, back)


def ask_count_photo(message):
    """
    Функция для запроса у пользователя количества фотографий, которые нужно показать для каждого отеля.
    Отправляет сообщение с просьбой ввести количество фотографий (не более 10)
    и регистрирует следующий шаг обработки сообщения.
    """
    activ_func[9] = 1
    activ_func_best[13] = 1
    mess = bot.send_message(message.chat.id, 'Сколько фотографий Вам показать? (не более 10)')
    bot.register_next_step_handler(mess, back)


def check_in_out(message):
    """
    Функция для обработки введенных пользователем дат заезда и выезда из отеля.
    Проверяет корректность формата введенных дат, вычисляет количество ночей и сохраняет информацию в словарь person_dict.
    В случае ошибки формата, запрашивает ввод дат заново.
    """
    activ_func[5] = 1
    activ_func_best[9] = 1

    if re.fullmatch(r'^\d\d\.\d\d\.\d{4}\s?-\s?\d\d\.\d\d\.\d{4}', message.text):
        check_in, check_out = re.split('-| - ', message.text)
        check_in = check_in.split('.')[::-1]
        check_out = check_out.split('.')[::-1]
        count_night = int(check_out[2]) - int(check_in[2])
        person_dict['checkIn'] = '-'.join(check_in)
        person_dict['checkOut'] = '-'.join(check_out)
        person_dict['count_night'] = count_night

        ask_count_hotel(message)
    else:
        bot.send_message(message.chat.id, 'Ошибка!\nС какого по какое число хотите остановиться?\n'
                                          '(ДД.ММ.ГГГГ - ДД.ММ.ГГГГ)')
        bot.register_next_step_handler(message, check_in_out)


def ask_count_hotel(message):
    """
    Функция для запроса у пользователя количества отелей, которые нужно показать.
    Отправляет сообщение с просьбой ввести количество отелей (не более 5) и регистрирует следующий шаг обработки сообщения.
    """
    activ_func[6] = 1
    activ_func_best[10] = 1
    bot.send_message(message.chat.id, 'Сколько отелей Вам показать? (не более 5)')
    bot.register_next_step_handler(message, back)


def count_hotel(message):
    """
    Функция для обработки введенного пользователем количества отелей.
    Проверяет корректность введенного значения, сохраняет его в словарь person_dict и запрашивает у пользователя
    необходимость загрузки фотографий для каждого отеля. В случае ошибки ввода, запрашивает ввод заново.
    """

    activ_func[7] = 1
    activ_func_best[11] = 1

    count_h = 5
    if re.fullmatch(r'^\d+', message.text):

        count = int(message.text)

        if count <= count_h:
            person_dict['count_hotel'] = count

            ask_photo(message)
        else:
            bot.send_message(message.chat.id, "Превышено количество отелей! Введите заново кол-во Отелей (не более 5)")
            bot.register_next_step_handler(message, count_hotel)


def ask_photo(message):
    """
    Функция для запроса у пользователя необходимости загрузки фотографий для каждого отеля.
    Отправляет сообщение с вариантами ответа "Да" и "Нет" и регистрирует callback-запросы для дальнейшей обработки.
    """
    activ_func[8] = 1
    activ_func_best[12] = 1
    keyboard = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text="Да", callback_data="yes")
    btn2 = types.InlineKeyboardButton(text="Нет", callback_data="no")
    keyboard.add(btn1, btn2)
    bot.send_message(message.chat.id, "Хотите загрузить фотографии для каждого отеля", reply_markup=keyboard)


def count_photo(message):
    """
    Функция для обработки введенного пользователем количества фотографий для каждого отеля.
    Проверяет корректность введенного значения, сохраняет его в словарь person_dict и вызывает функцию
    для отображения итоговых результатов. В случае ошибки ввода, запрашивает ввод заново.
    """
    activ_func[10] = 1
    activ_func_best[14] = 1

    count_p = 10
    if re.fullmatch(r'^\d+', message.text):
        count = int(message.text)
        if count <= count_p:
            person_dict['count_photo'] = int(message.text)
            total_result(message)
        else:
            bot.send_message(message.chat.id, 'Ошибка!\nВведите кол-во фотографий еще раз.(не более 10)')
            bot.register_next_step_handler(message, count_photo)


def range_price(message):
    """
    Функция для обработки введенного пользователем диапазона цен на отели.
    Проверяет корректность введенного значения, сохраняет его в словарь person_dict и вызывает функцию
    для запроса диапазона расстояний. В случае ошибки ввода, запрашивает ввод заново.
    """
    activ_func_best[5] = 1

    if re.fullmatch(r'^\d+\s?-\s?\d+', message.text):
        price = re.split('-| - ', message.text)
        person_dict['price_range'] = price
        ask_range_distance(message)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так\nВедите диапазон цен (от-до через -)')
        bot.register_next_step_handler(message, range_price)


def ask_range_distance(message):
    """
    Функция для запроса у пользователя желаемого диапазона расстояний от центра города до отелей.
    Отправляет сообщение с просьбой ввести диапазон расстояний и регистрирует следующий шаг обработки сообщения.
    """
    activ_func_best[6] = 1
    bot.send_message(message.chat.id, 'Введите желаемый диапазон расстояние от центра (от-до через -)')
    bot.register_next_step_handler(message, back)


def range_distance(message):
    """
    Функция для обработки введенного пользователем диапазона расстояний от центра города до отелей.
    Проверяет корректность введенного значения, сохраняет его в словарь person_dict и вызывает функцию
    для запроса дат заезда и выезда. В случае ошибки ввода, запрашивает ввод заново.
    """
    activ_func_best[7] = 1
    if re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)\s?-\s?(?:\d+(?:\.\d*)?|\.\d+)', message.text):
        distance = re.split('-| - ', message.text)
        person_dict['distance_range'] = distance
        data(message)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так\n'
                                          'Введите желаемый диапазон расстояние от центра (от-до через -)')
        bot.register_next_step_handler(message, range_distance)


def get_city_list(message):
    """
    Функция для получения списка городов на основе введенного пользователем запроса.
    Отправляет запрос к API для поиска локаций, обрабатывает ответ и возвращает словарь с названиями городов
    и их идентификаторами.
    """

    querystring = {"query": message.text, "locale": "ru_RU", 'currency': 'RUB'}
    headers = {
        "X-RapidAPI-Key": "ff0e0b452cmsh7eb9af29eeb85b1p1c4b5bjsn265a5659d883",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request(
        "GET", 'https://hotels4.p.rapidapi.com/locations/v2/search', headers=headers, params=querystring)

    data = json.loads(response.text)

    # with open('city1.test.json', 'w', encoding='utf-8') as file:
    #     json.dump(data, file, indent=4, ensure_ascii=False)

    city_dict = {', '.join((city['name'], re.findall('(\\w+)[\n<]', city['caption'] + '\n')[-1])): city['destinationId']
                 for city in data['suggestions'][0]['entities']}
    return city_dict


def total_result(message):
    """
    Функция для выполнения поиска отелей в заданном городе и отправки результатов пользователю.
    Определяет тип запроса (самые дешевые, самые дорогие или лучшие предложения) и вызывает соответствующую функцию
    для поиска отелей. Затем результаты отправляются пользователю.
    """
    bot.send_message(message.chat.id, 'Загружаю результаты...\nОдну минуту =)')
    city = hotel_search(message)
    if city is not None:
        if person_dict['func'] == 'low_price' or person_dict['func'] == '/low_price':
            city_list = low_price(city)
            message_to_user(message, city_list)
        elif person_dict['func'] == 'high_price' or person_dict['func'] == '/high_price':
            city_list = high_price(city)
            message_to_user(message, city_list)
        elif person_dict['func'] == 'best_deal' or person_dict['func'] == '/best_deal':
            city_list = best_deal(city)
            if not city_list:
                bot.send_message(message.chat.id, 'К сожалению по вашим критерием ничего не нашлось. '
                                                  'Попробуйте еще раз.\nНажмите /help')
            else:
                message_to_user(message, city_list)


def hotel_search(message):
    """
    Функция для выполнения поиска отелей в заданном городе с использованием API.
    Отправляет запрос к API, обрабатывает ответ и возвращает словарь с информацией об отелях.
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": person_dict['city_id'], "pageNumber": "1", "pageSize": "25",
                   "checkIn": person_dict['checkIn'], "checkOut": person_dict['checkOut'], "adults1": "1",
                   "sortOrder": "PRICE", "locale": "ru_RU", "currency": "RUB"}

    headers = {
        "X-RapidAPI-Key": "ff0e0b452cmsh7eb9af29eeb85b1p1c4b5bjsn265a5659d883",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    data = json.loads(response.text)

    # with open('city2.test.json', 'w', encoding='utf-8') as file:
    #     json.dump(data, file, indent=4, ensure_ascii=False)

    if data['result'] == 'OK':
        city = {}
        for dic in data['data']['body']['searchResults']['results']:
            city[dic['name']] = {
                'id': dic['id'],
                'starRating': dic['starRating'],
                'urls': dic['urls'],
                'address': '{}, {}, {}'.format(dic.get('address', {}).get('countryName', '-'),
                                               dic.get('address', {}).get('region', '-'),
                                               dic.get('address', {}).get('streetAddress', '-')),
                'guestReviews': dic.get('guestReviews', {}).get('unformattedRating', 'Нет оценки'),
                'distance': dic['landmarks'][0]['distance'],
                'price': dic.get('ratePlan', {}).get('price', {}).get('current', '-'),
                'exactCurrent': dic.get('ratePlan', {}).get('price', {}).get('exactCurrent', '-')
            }
        # with open('city3.test.json', 'w', encoding='utf-8') as file:
        #     json.dump(city, file, indent=4, ensure_ascii=False)

        return city
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так. Попробуйте еще раз.\nНажмите /start)')
        return None


def get_photo(id_hotel):
    """
    Функция для получения фотографий отеля по его идентификатору.
    Отправляет запрос к API, обрабатывает ответ и возвращает список URL-адресов фотографий.
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": id_hotel}

    headers = {
        "X-RapidAPI-Key": "ff0e0b452cmsh7eb9af29eeb85b1p1c4b5bjsn265a5659d883",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    photo = json.loads(response.text)

    photos_address = photo["hotelImages"][:person_dict['count_photo']]
    result = [photo['baseUrl'].replace('{size}', 'w') for photo in photos_address]

    # with open('foto1.json', 'a') as file:
    #     json.dump(result, file, indent=4, ensure_ascii=False)

    return result


def message_to_user(message, city_list):
    """
    Функция для отправки информации об отелях пользователю.
    Формирует сообщения с деталями отеля, включая фотографии, если пользователь запросил их,
    и отправляет эти сообщения пользователю. Также функция обновляет историю поиска и сбрасывает флаги активности функций.
    """
    text_hotel = []
    if person_dict['photo'] is True:
        for hotel_name, value in city_list.items():
            photos_address = get_photo(value['id'])
            total_sum = city_list[hotel_name]['exactCurrent'] * person_dict['count_night']
            mess = '*{name_h}*\n*Рейтинг*: {rey}\n*Адрес*: {address}\n*Расстояние от центра*: {distance}\n' \
                   '*Цена за ночь*: {price}\n*Кол-во ночей*: {count_night}\n' \
                   '*Стоимость проживания*: {total_price:.0f} RUB \n*Ссылка*: https://www.hotels.com/ho{link}'.format(
                name_h=hotel_name, address=city_list[hotel_name]['address'],
                distance=city_list[hotel_name]['distance'], price=city_list[hotel_name]['price'],
                rey=city_list[hotel_name]['guestReviews'], count_night=person_dict['count_night'],
                total_price=total_sum, link=city_list[hotel_name]['id']
            )
            text_hotel.append(mess)
            result = []
            for i_photo in photos_address:
                if not result:
                    result.append(types.InputMediaPhoto(caption=mess, media=i_photo, parse_mode='Markdown'))
                else:
                    result.append(types.InputMediaPhoto(media=i_photo))

            bot.send_media_group(message.chat.id, media=result)
            history_dct['result_hotel'][mess] = photos_address
        history_append(message)
        bot.send_message(message.chat.id, 'Поиск завершен!\nЧтобы начать сначала нажмите /help')
        for k in activ_func.keys():
            activ_func[k] = 0
        for k in activ_func_best.keys():
            activ_func_best[k] = 0

    else:
        for hotel_name, value in city_list.items():
            total_sum = city_list[hotel_name]['exactCurrent'] * person_dict['count_night']
            mess = '*{name_h}*\n*Рейтинг*: {rey}\n*Адрес*: {address}\n*Расстояние от центра*: {distance}\n' \
                   '*Цена за ночь*: {price}\n*Кол-во ночей*: {count_night}\n' \
                   '*Стоимость проживания*: {total_price:.0f} RUB\n*Ссылка*: https://www.hotels.com/ho{link}'.format(
                name_h=hotel_name, address=city_list[hotel_name]['address'],
                distance=city_list[hotel_name]['distance'], price=city_list[hotel_name]['price'],
                rey=city_list[hotel_name]['guestReviews'], count_night=person_dict['count_night'],
                total_price=total_sum, link=city_list[hotel_name]['id']
            )
            bot.send_message(message.chat.id, mess, parse_mode="Markdown")
            history_dct['result_hotel'][mess] = None
        history_append(message)
        bot.send_message(message.chat.id, 'Поиск завершен!\nЧтобы начать сначала нажмите /help')
        for k in activ_func.keys():
            activ_func[k] = 0
        for k in activ_func_best.keys():
            activ_func_best[k] = 0


def low_price(city_dict):
    """
    Функция для отбора отелей с наименьшими ценами из предоставленного словаря отелей.
    Ограничивает количество отелей до указанного пользователем значения и возвращает новый словарь с отобранными отелями.
    """

    result = list(city_dict.items())
    result = result[:person_dict['count_hotel']]
    result = dict(result)

    # with open('city4.test.json', 'w', encoding='utf-8') as file:
    #     json.dump(result, file, indent=4, ensure_ascii=False)

    return result


def high_price(city_dict):
    """
    Функция для отбора отелей с наибольшими ценами из предоставленного словаря отелей.
    Ограничивает количество отелей до указанного пользователем значения и возвращает новый словарь с отобранными отелями.
    """

    result = list(city_dict.items())
    result.reverse()
    result = result[:person_dict['count_hotel']]
    result = dict(result)

    # with open('city5.test.json', 'w', encoding='utf-8') as file:
    #     json.dump(result, file, indent=4, ensure_ascii=False)

    return result


def best_deal(city_dict):
    """
    Функция для отбора отелей, наиболее подходящих по заданным критериям расстояния от центра и цены.
    Фильтрует отели из предоставленного словаря отелей, ограничивает количество отелей
    до указанного пользователем значения и возвращает новый словарь с отобранными отелями.
    """
    result = {}
    for key, value in city_dict.items():
        dis = int(re.search(r'\d+', value['distance'])[0])
        min_r = int(person_dict['distance_range'][0])
        max_r = int(person_dict['distance_range'][1])
        pris = value['exactCurrent']
        min_p = int(person_dict['price_range'][0])
        max_p = int(person_dict['price_range'][1])

        if min_r <= dis <= max_r and min_p <= pris <= max_p:
            result[key] = value

    result = list(result.items())
    result = result[:person_dict['count_hotel']]
    result = dict(result)

    # with open('city6.test.json', 'w', encoding='utf-8') as file:
    #     json.dump(result, file, indent=4, ensure_ascii=False)

    return result


@exc_handler
def history_append(message):
    """
    Функция для добавления записи истории поиска отелей в JSON-файл.
    Добавляет текущую запись истории (history_dct) в список историй пользователя с указанным идентификатором чата.
    """
    person_id = str(message.chat.id)
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as file:
            dct = json.load(file)

        dct.setdefault(person_id, []).append(history_dct)

    with open('history.json', 'w', encoding='utf-8') as file:
        json.dump(dct, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
