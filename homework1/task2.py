# Зарегистрироваться на https://openweathermap.org/api и написать функцию,
# которая получает погоду в данный момент для города,
# название которого получается через input. https://openweathermap.org/current

import requests
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('API_KEY')


def get_city_temperature(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        temperature = json_data['main']['temp']
        return round(temperature - 273.15, 1)
    else:
        return None


if __name__ == '__main__':
    city_name = input('Enter city name please ')
    print(get_city_temperature(city_name))
