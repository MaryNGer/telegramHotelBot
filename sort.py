import json


with open('city2.json', 'r') as file:
    data = json.load(file)

city = {}
for dic in data['data']['body']['searchResults']['results']:
    city[dic['name']] = {
        'id': dic['id'],
        'starRating': dic['starRating'],
        'urls': dic['urls'],
        'address': '{}, {}, {}'.format(dic['address']['countryName'], dic['address']['region'], dic['address']['streetAddress']),
        'guestReviews': dic['guestReviews']['unformattedRating'],
        'distance': dic['landmarks'][0]['distance'],
        'price': dic['ratePlan']['price']['current']
    }


city = sorted(city.items(), key=lambda x: x[1]['guestReviews'], reverse=True)
city = dict(city)

with open('city3.json', 'w') as file:
    json.dump(city, file, indent=4, ensure_ascii=False)



