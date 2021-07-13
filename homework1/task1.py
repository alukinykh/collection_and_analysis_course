# Посмотреть документацию к API GitHub, разобраться как вывести список репозиториев для конкретного пользователя,
# сохранить JSON-вывод в файле *.json; написать функцию, возвращающую список репозиториев.

import requests
import json


def get_repositories_by_user(user):
    url = f'https://api.github.com/users/{user}/repos'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def save_get_results(user, data_json):
    with open(f'{user}.json', 'w') as write_f:
        json.dump(data_json, write_f)


def get_repo_list(data_json):
    for ind, item in enumerate(data_json):
        print(f"Репозиторий {ind + 1}: {item['name']}, {item['svn_url']}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    username = 'alukinykh'
    data_json = get_repositories_by_user(username)
    save_get_results(username, data_json)
    get_repo_list(data_json)