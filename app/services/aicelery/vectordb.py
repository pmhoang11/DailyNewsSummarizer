import os.path
from datetime import datetime

import duckdb
from celery import Task
from app.define import settings, news_folder
from app.schemas.vectordb import SaveVectorRequest, SaveVectorResponse
from app.services.aicelery.celery_app import app
from loguru import logger
from celery.exceptions import SoftTimeLimitExceeded

from app.services.aicelery.common import CeleryRedisClient
from app.services.crawl_news.summary_news import SummaryNews
from app.services.crawl_news.vectordb import VectorDB


class SummaryNewsTask(Task):
    """
    Abstraction of Celery's Task class
    """
    abstract = True

    def __init__(self):
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


@app.task(
    bind=True,
    base=SummaryNewsTask,
    name="{query}.{task_name}".format(
        query=settings.AI_QUERY_NAME,
        task_name=settings.SAVE_VECTOR_TASK
    ),
    time_limit = None,
    soft_time_limit = None
)
def save_vector_task(self, task_id: str, data: dict, request: dict):
    try:
        utc_now = datetime.utcnow()
        data['time']['start_generate'] = str(int(utc_now.timestamp()))
        CeleryRedisClient.started(task_id, data)

        vdb = VectorDB(settings.COLLECTION_NAME, settings.PERSIST_DIR)
        vdb.save_vector()
        response = SaveVectorResponse(collection_name=settings.COLLECTION_NAME)

        logger.info(response)
        CeleryRedisClient.success(task_id, data, response.__dict__)
        return

    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        err = {'code': "400", 'message': str(e)}
        CeleryRedisClient.failed(task_id, data, err)
        return
    except SoftTimeLimitExceeded:
        e = "Task was terminated after exceeding the time limit."
        logger.exception(str(e), exc_info=True)
        err = {'code': "500", 'message': "Internal Server Error"}
        CeleryRedisClient.failed(task_id, data, err)
        return
    except Exception as e:
        logger.exception(str(e), exc_info=True)
        err = {'code': "500", 'message': "Internal Server Error"}
        CeleryRedisClient.failed(task_id, data, err)
        return
