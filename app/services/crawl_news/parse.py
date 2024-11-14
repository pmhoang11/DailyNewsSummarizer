import re
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from loguru import logger
import requests
import pytz
from abc import ABC, abstractmethod

class ParseNews(ABC):
    @abstractmethod
    def process(self, html_content: str, url: str= '') -> dict:
        pass


class ParseNewsFactory:
    @staticmethod
    def get_articles_url(url: str) -> ParseNews:
        if "cnn.com" in url:
            return ParseNewsCNN()
        else:
            raise ValueError(f"Unsupported news source for URL: {url}")

class ParseNewsCNN(ParseNews):
    def __init__(self) -> None:
        self.html_path = ""
        try:
            pass

        except Exception as e:
            logger.exception(e)

    @staticmethod
    def _return_text_if_not_none(element) -> str:
        try:
            if element:
                return element.text.strip()
            else:
                return ''
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def _parse_timestamp(timestamp) -> '':
        rs = ''
        try:
            info = timestamp.split('\n')
            rs = info[1].strip()
        except Exception as e:
            logger.exception(e)
        return rs

    def _parse(self, html: str, url: str) -> dict:
        info = dict()
        try:
            soup = BeautifulSoup(html, features="html.parser")

            title = self._return_text_if_not_none(soup.find('h1', {'class': 'headline__text'}))
            author = soup.find('span', {'class': 'byline__name'})
            if not author:
                author = soup.find('span', {'class': 'byline__names'})
            author = self._return_text_if_not_none(author)

            content = self._return_text_if_not_none(soup.find('div', {'class': 'article__content'}))
            timestamp = self._return_text_if_not_none(soup.find('div', {'class': 'timestamp'}))
            timestamp = self._parse_timestamp(timestamp)

            category = url.split('/')[6]

            info = {
                "title": title,
                "category": category,
                "publish_datetime": timestamp,
                "content": content,
            }
        except Exception as e:
            logger.exception(e)
        return info

    def process(self, html_path:str, url: str = '') -> dict:
        parse_data = dict()
        try:
            self.html_path = html_path
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            parse_data = self._parse(html=html_content, url=url)

        except Exception as e:
            logger.exception(e)
        return parse_data

