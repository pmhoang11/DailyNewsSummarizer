import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

def news_folder(url: str):
    match url:
        case 'https://edition.cnn.com':
            fd = 'cnn'
        case _:
            fd = "other"
    return fd

class Settings(BaseSettings):
    NEWS_URL: str = os.getenv('NEWS_URL', 'https://edition.cnn.com')
    SAVE_RAW_DIR: str = os.getenv('SAVE_RAW_DIR', '/mnt/data/news')
    os.makedirs(SAVE_RAW_DIR, exist_ok=True)
    HOMPAGE_URLS = [
        'https://edition.cnn.com/',
    ]

    # URL DB
    NEWS_URL_DB_PATH: str = os.getenv('NEWS_URL_DB_PATH', '')

    AI_QUERY_NAME: str = os.getenv("AI_QUERY_NAME", "ai_celery")

    # CRAWL NEWS TASK
    CRAWL_TASK = os.getenv("CRAWL_TASK", "")
    SCHEDULE_TASK = os.getenv("SCHEDULE_TASK", "schedule_task")

    # SUMMARY NEWS TASK
    SUMMARY_NEWS_TASK = os.getenv("SUMMARY_NEWS_TASK", "")

    # SAVE VECTOR TASK
    SAVE_VECTOR_TASK = os.getenv("SAVE_VECTOR_TASK", "")

    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = os.getenv("RABBITMQ_PORT", 5672)
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASS: str = os.getenv("RABBITMQ_PASS", "guest")
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "")
    BROKER: str = "amqp://{user}:{pw}@{hostname}:{port}/{vhost}".format(
        user=RABBITMQ_USER,
        pw=RABBITMQ_PASS,
        hostname=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        vhost=RABBITMQ_VHOST,
    )

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = os.getenv("REDIS_PORT", 6379)
    REDIS_PASS: str = os.getenv("REDIS_PASS", "")
    REDIS_DB: int= os.getenv("REDIS_DB", 0)
    REDIS_BACKEND: str = "redis://{hostname}:{port}/{db}".format(
        hostname=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB
    )

    QUEUE_TIMEOUT = float(os.getenv("QUEUE_TIMEOUT", 1 * 10 * 60))

    # VectorDB
    PERSIST_DIR: str = os.getenv("PERSIST_DIR", "/mnt/data/news/vectorDB")
    os.makedirs(PERSIST_DIR, exist_ok=True)
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "news_vectorDB")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

settings = Settings()