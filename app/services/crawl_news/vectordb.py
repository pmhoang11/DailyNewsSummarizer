import glob
import os
from datetime import datetime

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever
from loguru import logger
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from typing import List, Optional, Dict
import duckdb

from langchain.text_splitter import RecursiveCharacterTextSplitter
import torch

from app.define import settings
from app.services.crawl_news.parse import ParseNewsFactory


class VectorDB:
    def __init__(self, collection_name: str, persist_directory: str) -> None:
        try:
            self.collection_name = collection_name
            self.persist_directory = persist_directory

            embedding_model = HuggingFaceEmbeddings(
                model_name='sentence-transformers/all-MiniLM-L6-v2',
                model_kwargs={'device': self.get_device()}
            )

            self.vector_db = Chroma(
                collection_name=collection_name,
                embedding_function=embedding_model,
                persist_directory=persist_directory
            )
            pass
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def get_device():
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def add_text(self, text: str, metadata: dict) -> None:
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", "(?<=\. )", " ", ""]
            )
            texts = splitter.split_text(text)

            self.vector_db.add_texts(
                texts=texts,
                metadatas=[
                              {
                                  'title': metadata['title'],
                                  'category': metadata['category'],
                                  'date': metadata['publish_datetime'],
                                  'crawl_date': metadata['crawl_date'],
                                  'url': metadata['url'],
                                  'source': metadata['source'],
                              }
                          ] * len(texts)
            )

        except Exception as e:
            logger.exception(e)

    def get_context(self, query: str, filter: Optional[Dict[str, str]] = None, ) -> List[Document]:
        try:
            docs_and_scores = self.vector_db.similarity_search_with_score(
                query=query,
                k=10,
                filter=filter
            )
            docs = []
            for doc, score in docs_and_scores:
                if score < 1.8:
                    docs.append(doc)

            return docs
        except Exception as e:
            logger.exception(e)

    def get_vectorstore(self):
        try:
            # return self.vector_db.as_retriever(search_kwargs={"k": 2})
            return self.vector_db
        except Exception as e:
            logger.exception(e)

    def save_vector(self):
        try:
            if not os.path.isfile(settings.NEWS_URL_DB_PATH):
                logger.info("news_url_db is not exist")
                return

            conn = duckdb.connect()

            conn.execute(f"CREATE TABLE crawl_news_db AS SELECT * FROM '{settings.NEWS_URL_DB_PATH}'")
            result = conn.execute(
                'SELECT url, path FROM crawl_news_db WHERE is_parse = False AND is_save = True').fetchall()

            for i, (url, path) in enumerate(result):
                try:
                    date_str = os.path.basename(os.path.dirname(path))
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    source_str = os.path.basename(os.path.dirname(os.path.dirname(path)))
                    logger.info("Save vector - {}: {}/{}".format(source_str, i + 1, len(result)))

                    par = ParseNewsFactory().get_articles_url(url)
                    info = par.process(path, url)
                    info['url'] = url
                    info['source'] = source_str
                    info_text = info['content']
                    info['crawl_date'] = date_obj.timestamp()

                    self.add_text(info_text, info)

                    conn.execute(
                        '''
                        UPDATE crawl_news_db
                        SET is_parse = True
                        WHERE url = ?
                        ''',
                        (url,)
                    )
                except Exception as e:
                    logger.exception(e)

            conn.execute(f"COPY crawl_news_db TO '{settings.NEWS_URL_DB_PATH}' (FORMAT 'parquet')")
            conn.close()
            logger.info("Save vector: Done")

        except Exception as e:
            logger.exception(e)
