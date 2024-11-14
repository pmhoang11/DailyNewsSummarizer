import os.path
import sys
import uuid
from datetime import datetime

import duckdb
from celery import Task
from app.define import settings, news_folder
from app.mq_main import celery_execute
# from app.mq_main import celery_execute
from app.schemas.crawl_news import QueueTimeHandle, QueueStatusHandle, QueueResult, CrawlNewsRequest
from app.services.aicelery.celery_app import app
from app.services.crawl_news.get_page import GetPageInfo, GetArticlesURLFactory
from loguru import logger
from celery.exceptions import SoftTimeLimitExceeded

from app.services.aicelery.common import CeleryRedisClient



class GetPageTask(Task):
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
    base=GetPageTask,
    name="{query}.{task_name}".format(
        query=settings.AI_QUERY_NAME,
        task_name=settings.CRAWL_TASK
    ),
    time_limit = None,
    soft_time_limit = None
)
def get_page_task(self, task_id: str, data: dict, request: dict):
    try:
        utc_now = datetime.utcnow()
        data['time']['start_generate'] = str(int(utc_now.timestamp()))
        CeleryRedisClient.started(task_id, data)

        hompage_url = request['url'].rstrip('/')

        gau = GetArticlesURLFactory.get_articles_url(hompage_url)
        news_list = gau.process()

        # region check url in db
        # region init db
        conn = duckdb.connect()

        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS crawl_news_db (
            url VARCHAR PRIMARY KEY,
            title VARCHAR,
            path VARCHAR,
            source VARCHAR,
            is_save BOOLEAN DEFAULT FALSE,
            is_parse BOOLEAN DEFAULT FALSE,
        )
        '''
        if os.path.isfile(settings.NEWS_URL_DB_PATH):
            conn.execute(create_table_sql)
            conn.execute(f'''
            INSERT INTO crawl_news_db
            SELECT *
            FROM read_parquet('{settings.NEWS_URL_DB_PATH}')
            ''')

        else:
            os.makedirs(os.path.dirname(settings.NEWS_URL_DB_PATH), exist_ok=True)
            conn.execute(create_table_sql)
            conn.execute(f"COPY crawl_news_db TO '{settings.NEWS_URL_DB_PATH}' (FORMAT 'parquet')")

        # endregion init db

        news_list_valid = []
        for url in news_list:
            if not is_crawled_url(conn, url):
                news_list_valid.append(url)
        # endregion check url

        folder = news_folder(hompage_url)
        save_dir = os.path.join(settings.SAVE_RAW_DIR, folder, utc_now.strftime("%Y%m%d"))
        os.makedirs(save_dir, exist_ok=True)
        save_dir = str(save_dir)

        # region save html raw
        for i, news in enumerate(news_list_valid):
            try:
                logger.info("{}: {}/{}".format(folder, i+1, len(news_list_valid)))
                gpi = GetPageInfo(news, save_dir)
                page_data = gpi.process()
                conn.execute(
                    'INSERT INTO crawl_news_db (url, title, path, source, is_save, is_parse) VALUES (?, ?, ?, ?, ?, ?)',
                    (news, page_data['title'], page_data['path'], folder, True, False)
                )

            except Exception as e:
                logger.exception(e)
        # endregion save html raw

        conn.execute(f"COPY crawl_news_db TO '{settings.NEWS_URL_DB_PATH}' (FORMAT 'parquet')")
        conn.close()

        response = {
            'url': request['url'],
            'dir': save_dir
        }

        logger.info(response)
        CeleryRedisClient.success(task_id, data, response)
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


@app.task(
    bind=True,
    base=GetPageTask,
    name="{query}.{task_name}".format(
        query=settings.AI_QUERY_NAME,
        task_name=settings.SCHEDULE_TASK
    ),
    time_limit=None,
    soft_time_limit=None
)
def schedule_task(self):
    try:
        data = create_task_id()
        CeleryRedisClient.started(data['task_id'], data)

        hompage_urls = settings.HOMPAGE_URLS

        for hompage_url in hompage_urls:

            rq = CrawlNewsRequest(url=hompage_url)
            task_save_raw_html = create_task_id()

            celery_execute.send_task(
                name="{}.{}".format(settings.AI_QUERY_NAME, settings.CRAWL_TASK),
                kwargs={
                    'task_id': task_save_raw_html['task_id'],
                    'data': task_save_raw_html,
                    'request': rq.__dict__
                },
                queue=settings.AI_QUERY_NAME
            ).get()

        task_save_vector = create_task_id()
        celery_execute.send_task(
            name="{}.{}".format(settings.AI_QUERY_NAME, settings.SAVE_VECTOR_TASK),
            kwargs={
                'task_id': task_save_vector['task_id'],
                'data': task_save_vector,
                'request': dict()
            },
            queue=settings.AI_QUERY_NAME
        ).get()

        response = {
            'status': 'schedule_task done'
        }

        logger.info(response)
        CeleryRedisClient.success(data['task_id'], data, response)
        logger.info('!!! END cron')
        return

    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        return
    except SoftTimeLimitExceeded:
        e = "Task was terminated after exceeding the time limit."
        logger.exception(str(e), exc_info=True)
        return
    except Exception as e:
        logger.exception(str(e), exc_info=True)
        return




def is_crawled_url (conn, url: str) -> bool:
    result = conn.execute('SELECT COUNT(*) FROM crawl_news_db WHERE url = ?', (url,)).fetchone()
    if result:
        if result[0] == 0:
            check = False
        else:
            check = True
    else:
        check = False
    return check

def create_task_id():
    utc_now = datetime.utcnow()
    task_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_OID,
            settings.AI_QUERY_NAME + "_" + str(utc_now.strftime("%Y%m%d%H%M%S%f")),
        )
    )
    time_handle = QueueTimeHandle().__dict__
    status_handle = QueueStatusHandle().__dict__
    data = QueueResult(task_id=task_id, time=time_handle, status=status_handle)
    data = data.__dict__

    data['time']['start_generate'] = str(int(utc_now.timestamp()))
    return data