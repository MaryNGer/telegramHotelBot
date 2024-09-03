import requests
from pprint import pprint
import json

url = "https://hotels4.p.rapidapi.com/locations/v2/search"

querystring = {"query": "moscow", "locale": "en_US", "currency": "USD"}

headers = {
    "X-RapidAPI-Key": "ff0e0b452cmsh7eb9af29eeb85b1p1c4b5bjsn265a5659d883",
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)

data = json.loads(response.text)

x = data['suggestions'][1]['entities']

with open('text2.json', 'w') as file:
    json.dump(x, file, indent=4)

print(response.text)
