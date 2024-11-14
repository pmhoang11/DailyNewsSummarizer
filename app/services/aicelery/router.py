from app.define import settings
from app.services.aicelery.init_broker import is_broker_running
from app.services.aicelery.init_redis import is_backend_running
from app.services.aicelery.celery_app import app

if not is_backend_running():
    exit()
if not is_broker_running():
    exit()

app.conf.task_routes = {
    'tasks.get_page_task': {'queue': settings.AI_QUERY_NAME},
    'tasks.summary_news_task': {'queue': settings.AI_QUERY_NAME},
    'tasks.save_vector_task': {'queue': settings.AI_QUERY_NAME},
    'tasks.schedule_task': {'queue': settings.AI_QUERY_NAME},
}

from app.services.aicelery.crawl_news import get_page_task
from app.services.aicelery.summary_news import summary_news_task
from app.services.aicelery.vectordb import save_vector_task
from app.services.aicelery.crawl_news import schedule_task
