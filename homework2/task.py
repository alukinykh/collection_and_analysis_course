# Необходимо собрать информацию о вакансиях на вводимую должность (используем input)
# с сайтов Superjob(необязательно) и HH(обязательно).
# Приложение должно анализировать несколько страниц сайта (также вводим через input).
# Получившийся список должен содержать в себе минимум:
# 1) Наименование вакансии.
# 2) Предлагаемую зарплату (отдельно минимальную и максимальную).
# 3) Ссылку на саму вакансию.
# 4) Сайт, откуда собрана вакансия.
#
# По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение).
# Структура должна быть одинаковая для вакансий с обоих сайтов. Сохраните результат в json-файл

import time
import re
import json
import requests
from bs4 import BeautifulSoup


class HHParser:
    """Parse hh.ru"""
    search_link = "https://hh.ru/search/vacancy?text="
    vacancies = []

    def __init__(self, position, pages):
        """Init class."""
        self.position = position
        self.pages = pages
        self.get_vacancies()

    def get_vacancies(self):
        "Request vacancies from hh.ru"
        request_link = self.search_link + self.position.replace(" ", "+")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) \
                           Gecko/20100101 Firefox/42.0"
        }
        request = requests.get(request_link, headers=headers)
        self.pages = min(self.get_pages_count(request.text), self.pages)
        self.parse_page(request.text)

        for page_num in range(1, self.pages):
            time.sleep(1)
            request_link = self.search_link + self.position.replace(" ", "+") + \
                                                            "&page=" + str(page_num)
            request = requests.get(request_link, headers=headers)
            self.parse_page(request.text)

    def get_pages_count(self, page_html):
        """Get pages count."""
        soup = BeautifulSoup(page_html, 'html.parser')
        pagers = soup.find_all("a", {"data-qa": "pager-page"})
        pages_count = 0
        if pagers is not None:
            last_pager = pagers[-1]
            last_pager = last_pager.find("span")
            if last_pager is not None:
                pages_count = int(last_pager.text)
        return pages_count

    def parse_page(self, page_html):
        """Parse one page."""
        soup = BeautifulSoup(page_html, 'html.parser')

        vacancies = soup.find_all("div", {"class": "vacancy-serp-item"})
        for vacancy in vacancies:
            new_vacancy = {}
            title_link = vacancy.find("a", {"data-qa": "vacancy-serp__vacancy-title"})
            new_vacancy["title"] = title_link.text
            new_vacancy["link"] = title_link["href"]

            compensation = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-compensation"})
            new_vacancy["min_compensation"] = None
            new_vacancy["max_compensation"] = None
            if compensation is not None:
                compensation = compensation.text.replace("\u202f", "")
                if compensation.startswith("до"):
                    new_vacancy["max_compensation"] = compensation[3:]
                elif compensation.startswith("от"):
                    new_vacancy["min_compensation"] = compensation[3:]
                else:
                    new_vacancy["min_compensation"] = compensation
                    compensation_match = re.match(
                        r"(?P<min>[0-9]+) – (?P<max>[0-9]+) (?P<currency>.*)",
                        compensation
                    )
                    currency = compensation_match.group("currency")
                    new_vacancy["min_compensation"] = compensation_match.group("min") + \
                                                                            " " + currency
                    new_vacancy["max_compensation"] = compensation_match.group("max") + \
                                                                            " " + currency

            new_vacancy["website"] = "hh.ru"
            self.vacancies.append(new_vacancy)

    def save_to_json(self, file_path):
        """Save result to json."""
        with open(file_path, "w") as json_file:
            json.dump(self.vacancies, json_file)


if __name__ == "__main__":
    hh_parser = HHParser(input("Position: "), int(input("Pages: ")))
    hh_parser.save_to_json("result.json")