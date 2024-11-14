from datetime import datetime, timedelta
from typing import Optional, Dict

import pytz
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from loguru import logger

from app.define import settings
from app.services.crawl_news.vectordb import VectorDB
from langchain_community.chat_models import ChatOpenAI


class SummaryNews(object):
    __instance = None

    def _get_llm(self) -> BaseLanguageModel:
        try:
            llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model_name="gpt-4o",
                temperature=0.3,
                request_timeout=120,
                max_retries=10
            )
            return llm
        except Exception as e:
            logger.exception(e)

    def _get_documents(self, query: str, filter: Optional[Dict[str, str]] = None):
        try:
            vectorstore = VectorDB(settings.COLLECTION_NAME, settings.PERSIST_DIR)
            docs = vectorstore.get_context(query=query, filter=filter)

            for doc in docs:
                metadata = doc.metadata
                title = metadata.get("title", "")
                date = metadata.get("date", "")
                link = metadata.get("url", "")
                category = metadata.get("category", "")
                content = doc.page_content

                combined_content = f"""
                    Title: {title}
                    Link: {link}                   
                    Published on: {date}
                    Category: {category}
                    
                    Content:
                    {content}

                   """
                doc.page_content = combined_content

            return docs
        except Exception as e:
            logger.exception(e)

    def _get_prompt(self):
        try:
            prompt_template = """
                I want you to act as an AI news assistant. Below is a list of news articles retrieved from the database for today. Please summarize them into a concise daily news summary, ensuring that the most important information is retained.
            
                List of news articles:
            
                {context}
            
                Instructions:
                - First, provide a summary that highlights the most important events of the day across all the articles.
                - Then, provide a brief summary for each individual news article, including the article's link and publish date.
                - Make sure the summaries are structured clearly, with separate sections for each article.
                """

            prompt = PromptTemplate(template=prompt_template, input_variables=["context"])

            return prompt
        except Exception as e:
            logger.exception(e)

    def _load_chain(self):
        try:
            llm = self._get_llm()
            prompt = self._get_prompt()
            qa_chain = load_qa_chain(
                llm=llm,
                chain_type="stuff",
                prompt=prompt,
            )
            return qa_chain
        except Exception as e:
            logger.exception(e)

    def process(self, tag: str, filter: Optional[Dict[str, str]] = None) -> str:
        try:
            date_thr = (datetime.now(pytz.utc) - timedelta(days=3)).timestamp()

            if filter is None:
                filter = {
                    'crawl_date': {"$gte": date_thr}
                }

            query = "Topic: {}".format(tag)
            docs = self._get_documents(query=query, filter=filter)

            qa_chain = self._load_chain()
            output = qa_chain.invoke({'input_documents': docs})
            answer = output['output_text']

            return answer
        except Exception as e:
            logger.exception(e)
