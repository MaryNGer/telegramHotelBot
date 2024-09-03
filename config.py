from main import (
    help_func, ask_city, search_by_city, data, check_in_out, ask_count_hotel,
    count_hotel, ask_photo, ask_count_photo, count_photo, ask_range_price, range_price,
    ask_range_distance, range_distance
)

history_dct = {
    'person_id': '',
    'func': '',
    'time': '',
    'result_photo': [],
    'result_hotel': {}
}
person_dict = {
    'func': None,
    'city_id': '',
    'count_hotel': 0,
    'count_night': 0,
    'price_range': [],
    'distance_range': [],
    'photo': False,
    'count_photo': 0,
    'checkIn': '',
    'checkOut': '',
}

func = {1: help_func,
        2: ask_city,
        3: search_by_city,
        4: data,
        5: check_in_out,
        6: ask_count_hotel,
        7: count_hotel,
        8: ask_photo,
        9: ask_count_photo,
        10: count_photo
        }

activ_func = {1: 0,
              2: 0,
              3: 0, # пропустить
              4: 0,
              5: 0,
              6: 0,
              7: 0,
              8: 0,
              9: 0,
              10: 0
              }

func_best = {
        1: help_func,
        2: ask_city,
        3: search_by_city,
        4: ask_range_price,
        5: range_price,
        6: ask_range_distance,
        7: range_distance,
        8: data,
        9: check_in_out,
        10: ask_count_hotel,
        11: count_hotel,
        12: ask_photo,
        13: ask_count_photo,
        14: count_photo
}

activ_func_best = {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 0,
    8: 0,
    9: 0,
    10: 0,
    11: 0,
    12: 0,
    13: 0,
    14: 0
}