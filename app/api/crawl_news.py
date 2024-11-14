import io
import logging
import json
import os
import uuid
from datetime import datetime

from typing import Any
from typing import Optional

from fastapi import APIRouter, Depends

from app.define import settings
from app.mq_main import celery_execute, redis
from app.schemas.crawl_news import QueueTimeHandle, QueueStatusHandle, QueueResult, QueueResponse, CrawlNewsRequest
from app.schemas.base import DataResponse


logger = logging.getLogger()
router = APIRouter()


@router.post(
    "/crawl_news",
    response_model=DataResponse[QueueResponse],
)
def crawl_news_html(request: CrawlNewsRequest):
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
    data_dump = json.dumps(data.__dict__)

    redis.set(task_id, json.dumps(data_dump))

    # generations_in_queue
    celery_execute.send_task(
        name="{}.{}".format(settings.AI_QUERY_NAME, settings.CRAWL_TASK),
        kwargs={
            'task_id': task_id,
            'data': data.__dict__,
            'request': request
        },
        queue=settings.AI_QUERY_NAME
    )

    return DataResponse().success_response(
        data=QueueResponse(status="PENDING", time=utc_now, task_id=task_id)
    )
