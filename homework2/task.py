"""
Эта дз является доработкой дз из второго урока; продолжаем работать с hh ru
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
записывающую собранные вакансии в созданную БД(добавление данных в БД по ходу сбора данных).
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой
больше введённой суммы. Необязательно - возможность выбрать вакансии без указанных зарплат
3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.
"""

import time
import re
import pprint
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup


class HHParser:
    """Parse hh.ru"""
    search_link = "https://hh.ru/search/vacancy?text="
    mongo_client = MongoClient()
    hh_parser_db = mongo_client.hh_parser_db
    vacancies_collection = hh_parser_db.vacancies

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

    def parse_compensation(self, compensation):
        """Parse compensation."""
        min_compensation = None
        max_compensation = None
        compensation_currency = None
        if compensation is not None:
            compensation = compensation.text.replace("\u202f", "")
            if compensation.startswith("до"):
                compensation_match = re.match(
                    r"(.*) (?P<compensation>[0-9]+) (?P<currency>.*)",
                    compensation
                )
                max_compensation = int(compensation_match.group("compensation"))
                compensation_currency = compensation_match.group("currency")
            elif compensation.startswith("от"):
                compensation_match = re.match(
                    r"(.*) (?P<compensation>[0-9]+) (?P<currency>.*)",
                    compensation
                )
                min_compensation = int(compensation_match.group("compensation"))
                compensation_currency = compensation_match.group("currency")
            else:
                compensation_match = re.match(
                    r"(?P<min>[0-9]+) – (?P<max>[0-9]+) (?P<currency>.*)",
                    compensation
                )
                min_compensation = int(compensation_match.group("min"))
                max_compensation = int(compensation_match.group("max"))
                compensation_currency = compensation_match.group("currency")

        return (min_compensation, max_compensation, compensation_currency)

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
            new_vacancy["min_compensation"], new_vacancy["max_compensation"], \
            new_vacancy["compensation_currency"] = self.parse_compensation(compensation)

            new_vacancy["website"] = "hh.ru"
            self.vacancies_collection.update_one(new_vacancy, {"$set": new_vacancy}, upsert=True)

    def print_salary_gt(self, min_salary):
        """Print vacancies with salary greater than min_salary"""
        for vacancy in self.vacancies_collection.find({"min_compensation": {"$gt": min_salary}}):
            pprint.pprint(vacancy)


if __name__ == "__main__":
    hh_parser = HHParser(input("Position: "), int(input("Pages: ")))
    hh_parser.print_salary_gt(int(input("Print vacancies with salary greater than: ")))