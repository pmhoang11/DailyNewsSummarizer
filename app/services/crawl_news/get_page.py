import os
import re
from datetime import datetime

from bs4 import BeautifulSoup
from loguru import logger
import requests
from abc import ABC, abstractmethod


class GetArticlesURL(ABC):
    HEADERS: dict = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache'
    }
    @abstractmethod
    def process(self) -> list:
        pass


class GetArticlesURLFactory:
    @staticmethod
    def get_articles_url(url: str) -> GetArticlesURL:
        if "edition.cnn.com" in url:
            return GetArticlesUrlCNN()
        else:
            raise ValueError(f"Unsupported news source for URL: {url}")


class GetArticlesUrlCNN(GetArticlesURL):
    def __init__(self) -> None:
        try:
            self.news_url = 'https://edition.cnn.com'
            self.today_str = datetime.now().strftime('%Y/%m')

        except Exception as e:
            logger.exception(e)

    def _get_links(self, html: str):
        all_urls = list()
        try:
            soup = BeautifulSoup(html, features="html.parser")
            ls = soup.find_all(
                'a',
                {
                    'href': re.compile("^/"),
                }
            )
            all_urls = list(map(lambda x: self.news_url + x['href'], filter(lambda x: '/gallery/' not in x['href'] and self.today_str in x['href'], ls)))

        except Exception as e:
            logger.exception(e)
        return all_urls

    def process(self) -> list:
        article_urls = list()
        try:
            response = requests.get(self.news_url, headers=self.HEADERS)
            urls = self._get_links(response.text)
            article_urls = list(set(urls))

        except Exception as e:
            logger.exception(e)
        return article_urls


class GetPageInfo:
    HEADERS: dict = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache'
    }

    def __init__(self, news_url:str, save_raw_dir:str) -> None:
        try:
            self.news_url = news_url
            self.save_raw_dir = save_raw_dir
        except Exception as e:
            logger.exception(e)

    def process(self) -> dict:
        parse_data = dict()
        try:
            response = requests.get(self.news_url, headers=self.HEADERS)
            raw_data = response.text
            soup = BeautifulSoup(response.text, features="html.parser")

            title = soup.title.text
            parse_data['title'] = title.strip().replace('/', '_')
            # region save raw html
            path = os.path.join(self.save_raw_dir, '{}.html'.format(parse_data['title']))
            with open(path, 'w') as f:
                f.write(raw_data)
            # endregion save raw html
            parse_data['path'] = path

        except Exception as e:
            logger.exception(e)
        return parse_data
