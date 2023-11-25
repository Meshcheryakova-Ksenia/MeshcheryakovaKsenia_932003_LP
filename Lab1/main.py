import requests
from bs4 import BeautifulSoup
from threading import Thread, Event
from queue import Queue
import time
import signal

class News(Thread):
    def __init__(self, url, update_interval, news_queue, stop_event, scraper_function):
        super().__init__()
        self.url = url
        self.update_interval = update_interval
        self.news_queue = news_queue
        self.stop_event = stop_event
        self.seen_news = {}
        self.scraper_function = scraper_function

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.scraper_function()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                self.stop_event.set()

    def update_news1(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for news_item in soup.find_all('div', class_="sc-k5zf9p-13 fsrrpT"):
            title = news_item.find('a', class_="sc-k5zf9p-3 dqylVG")
            abstract = news_item.find('a', class_="sc-n7hj2k-0 fBNHbX")
            author = news_item.find('time', class_="sc-k5zf9p-10 eCBTtM")

            if title not in self.seen_news:
                self.seen_news[title] = (author, abstract)
                self.news_queue.put({'url': self.url, 'title': title, 'author': author, 'abstract': abstract})

    def update_news2(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for news_item in soup.find_all('section', class_="gd-container"):
            title = news_item.find('a', class_="title")
            abstract = news_item.find('li', class_="secondary-calling")
            author = news_item.find('div', class_="ex-ig")

            if title not in self.seen_news:
                self.seen_news[title] = (author, abstract)
                self.news_queue.put({'url': self.url, 'title': title, 'author': author, 'abstract': abstract})

    def update_news3(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for news_item in soup.find_all('section', class_="zone zone--zoneB zone--layout-layout2 zone--theme-default zone--has-title js-cet-subunit"):
            title = news_item.find('h3', class_="card__headline__text")
            abstract = news_item.find('div', class_="card__description")
            author = news_item.find('span', class_="card__byline__author__name-title")

            if title not in self.seen_news:
                self.seen_news[title] = (author, abstract)
                self.news_queue.put({'url': self.url, 'title': title, 'author': author, 'abstract': abstract})

def print_news(news_queue):
    while True:
        news_item = news_queue.get()
        if news_item is None:
            break
        title = news_item['title'].get_text().strip() if news_item['title'] else "Нет заголовка"
        author = news_item['author'].get_text().strip() if news_item['author'] else "Автор неизвестен"
        abstract = news_item['abstract'].get_text().strip() if news_item['abstract'] else "Нет аннотации"
        print(f"Сайт: {news_item['url']}\nЗаголовок: {title}\nРаздел: {abstract}\nДополнительная информация: {author}\n---")
       
if __name__ == "__main__":
    news_queue = Queue()
    stop_event = Event()

    scrapers = [
        News("https://www.kaliningrad.kp.ru", 60, news_queue, stop_event, lambda: scraper.update_news1()),
        News("https://www.ig.com.br/?utm_source=vsesmi_online", 60, news_queue, stop_event, lambda: scraper.update_news2()),
        News("https://www.huffingtonpost.jp", 60, news_queue, stop_event, lambda: scraper.update_news3()),
    ]

    for scraper in scrapers:
        scraper.start()

    print_thread = Thread(target=print_news, args=(news_queue,))
    print_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nЗавершение работы по Ctrl-C")
        stop_event.set()
        for _ in range(len(scrapers)): 
            news_queue.put(None)
        for scraper in scrapers:
            scraper.join()
        print_thread.join()
