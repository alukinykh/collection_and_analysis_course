"""
Написать программу, которая собирает посты из группы https://vk.com/tokyofashion
Будьте внимательны к сайту!
Делайте задержки, не делайте частых запросов!
1) В программе должен быть ввод, который передается в поисковую строку по постам группы
2) Соберите данные постов:
- Дата поста
- Текст поста
- Ссылка на пост(полная)
- Ссылки на изображения(если они есть; необязательно)
- Количество лайков, "поделиться" и просмотров поста
3) Сохраните собранные данные в MongoDB
4) Скролльте страницу, чтобы получить больше постов(хотя бы 2-3 раза)
5) (Дополнительно, необязательно) Придумайте как можно скроллить "до конца" до тех пор пока
посты не перестанут добавляться
Чем пользоваться?
Selenium, можно пользоваться lxml, BeautifulSoup
"""

import time

from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class TokyoFashionScrapper:
    """Searcg in https://vk.com/tokyofashion"""
    url = "https://vk.com/tokyofashion"
    post_link = "https://vk.com/wall"
    scroll_pause_time = 1
    posts = []

    def __init__(self, search_query):
        self.search_query = search_query
        mongo_client = MongoClient()
        self.posts_db = mongo_client.tokyofashion.posts

    def load(self):
        """Load page."""
        driver = webdriver.Chrome()
        driver.get(self.url)

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//*[@id='wall_tabs']/li[@class='ui_tab_search_wrap']/a"
            ))
        )
        element.click()

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "wall_search"))
        )

        element.send_keys(self.search_query)
        element.send_keys(Keys.ENTER)
        time.sleep(self.scroll_pause_time)

        last_height = driver.execute_script("return document.body.scrollHeight")
        # Scroll max 10 times
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        posts_elems = driver.find_elements_by_xpath("//div[@class='_post_content']")
        for element in posts_elems:
            if not element.is_displayed():
                continue

            new_post = {}
            parent_id = element.find_element_by_xpath("./..").get_attribute("data-post-id")
            post_full_link = self.post_link + parent_id
            new_post["link"] = post_full_link
            date_span = element.find_element_by_xpath(
                ".//div[@class='post_date']//span[@class='rel_date']"
            )
            new_post["date"] = date_span.get_attribute('textContent')
            text_div = element.find_element_by_xpath(".//div[@class='wall_post_text']")
            new_post["text"] = text_div.get_attribute('textContent')
            like_count = element.find_element_by_xpath(
                ".//a[contains(@class, 'like')]/div[@class='like_button_count']"
            )
            new_post["likes"] = like_count.get_attribute('textContent')
            reposts_count = element.find_element_by_xpath(
                ".//a[contains(@class, 'share')]/div[@class='like_button_count']"
            )
            new_post["reposts"] = reposts_count.get_attribute('textContent')
            views_count = element.find_element_by_xpath(".//div[contains(@class, '_views')]")
            new_post["views"] = views_count.get_attribute('textContent')

            self.posts.append(new_post)

        driver.quit()

    def db_write(self):
        """Write posts into db."""
        for post in self.posts:
            self.posts_db.update_one(post, {"$set": post}, upsert=True)


if __name__ == "__main__":
    scrapper = TokyoFashionScrapper(input("Search query: "))
    scrapper.load()
    scrapper.db_write()
