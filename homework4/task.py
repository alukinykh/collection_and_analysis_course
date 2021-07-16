"""
1) Написать приложение, которое собирает основные новости с сайтов news.mail.ru,
lenta.ru, yandex.news
Для парсинга использовать xpath. Структура данных должна содержать:
- название источника(оригинального источника),
- наименование новости,
- ссылку на новость,
- дата публикации
Нельзя использовать BeautifulSoup
2) Сложить все новости в БД(Mongo); без дубликатов, с обновлениями
"""

import requests
from lxml import html
from pymongo import MongoClient


class MongoWriter:
    """Write news into mongo."""

    def __init__(self):
        mongo_client = MongoClient()
        self.news = mongo_client.news_db.news

    def write(self, news_list):
        """Write news list into db."""
        for news_piece in news_list:
            self.news.update_one(news_piece, {"$set": news_piece}, upsert=True)


class NewsParser:
    """Parse news."""

    def __init__(self, url, article_xpath, link_xpath,
                 link_title_xpath, link_href_xpath, source_xpath,
                 source_title_xpath, source_time_xpath,
                 source_time_extra_xpath=None):
        self.url = url
        self.article_xpath = article_xpath
        self.link_xpath = link_xpath
        self.link_title_xpath = link_title_xpath
        self.link_href_xpath = link_href_xpath
        self.source_xpath = source_xpath
        self.source_title_xpath = source_title_xpath
        self.source_time_xpath = source_time_xpath
        self.source_time_extra_xpath = source_time_extra_xpath
        self.news = []

    def parse(self):
        """Actual parse."""
        self.news.clear()
        headers = {"Content-Type": "text/html", }
        response = requests.get(self.url, headers=headers)
        tree = html.fromstring(response.text)
        for article in tree.xpath(self.article_xpath):
            next_news = {
                "source": "",
                "title": "",
                "link": "",
                "time": ""
                }
            link_elem = article.xpath(self.link_xpath)
            if len(link_elem) > 0:
                link_elem = link_elem[0]
                title = link_elem.xpath(self.link_title_xpath)
                if len(title) > 0:
                    next_news["title"] = title[0]
                link = link_elem.xpath(self.link_href_xpath)
                if len(link) > 0:
                    next_news["link"] = link[0]
                    if not next_news["link"].startswith("https://") and \
                              not next_news["link"].startswith("http://"):
                        next_news["link"] = self.url + next_news["link"]
            source_elem = article.xpath(self.source_xpath)
            if len(source_elem) > 0:
                source_elem = source_elem[0]
                time = source_elem.xpath(self.source_time_xpath)
                if len(time) > 0:
                    next_news["time"] = time[0]
                    if self.source_time_extra_xpath is not None:
                        time = source_elem.xpath(self.source_time_extra_xpath)
                        if len(time) > 0:
                            next_news["time"] = next_news["time"] + " " + time[0]
                if self.source_title_xpath is not None:
                    source = source_elem.xpath(self.source_title_xpath)
                    if len(source) > 0:
                        next_news["source"] = source[0]
                else:
                    next_news["source"] = self.url
            self.news.append(next_news)


class YandexNewsParser(NewsParser):
    """Parse news from yandex."""

    def __init__(self):
        super().__init__(
            url="https://yandex.ru/news",
            article_xpath="//article[contains(@class, 'mg-card')]",
            link_xpath=".//a[contains(@class, 'mg-card__link')]",
            link_title_xpath="./descendant::node()/text()",
            link_href_xpath="./@href",
            source_xpath=".//div[contains(@class, 'mg-card-source')]",
            source_title_xpath="./span[contains(@class, 'mg-card-source__source')]//\
                a[contains(@class, 'mg-card__source-link')]/text()",
            source_time_xpath="./span[contains(@class, 'mg-card-source__time')]/text()"
        )


class MailNewsParser(NewsParser):
    """Parse news from mail.ru."""

    def __init__(self):
        super().__init__(
            url="https://news.mail.ru",
            article_xpath="//div[contains(@class, 'newsitem') \
                 and not(contains(@class, 'newsitem__params'))]",
            link_xpath=".//a[contains(@class, 'newsitem__title')]",
            link_title_xpath="./descendant::node()/text()",
            link_href_xpath="./@href",
            source_xpath=".//div[contains(@class, 'newsitem__params')]",
            source_title_xpath="./span[not(contains(@class, 'js-ago'))]/text()",
            source_time_xpath="./span[contains(@class, 'js-ago')]/@datetime"
        )


class LentaNewsParser(NewsParser):
    """Parse news from yandex."""

    def __init__(self):
        super().__init__(
            url="https://lenta.ru",
            article_xpath="//div[contains(@class, 'item news')]",
            link_xpath=".//a[contains(@class, 'titles')]",
            link_title_xpath="./descendant::node()/text()",
            link_href_xpath="./@href",
            source_xpath=".//span[contains(@class, 'item__date')]",
            source_title_xpath=None,
            source_time_xpath="./text()",
            source_time_extra_xpath="./span[contains(@class, 'time')]/text()"
        )


if __name__ == "__main__":
    db_writer = MongoWriter()

    ya_parser = YandexNewsParser()
    ya_parser.parse()
    db_writer.write(ya_parser.news)

    mail_parser = MailNewsParser()
    mail_parser.parse()
    db_writer.write(mail_parser.news)

    lenta_parser = LentaNewsParser()
    lenta_parser.parse()
    db_writer.write(lenta_parser.news)


