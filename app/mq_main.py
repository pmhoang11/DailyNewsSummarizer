from redis import Redis
from app.define import settings
from celery import Celery


redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASS, db=settings.REDIS_DB)

celery_execute = Celery(broker=settings.BROKER, backend=settings.REDIS_BACKEND)
