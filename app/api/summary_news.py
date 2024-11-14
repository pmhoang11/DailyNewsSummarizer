import logging
from typing import Any, Optional

from app.schemas.base import DataResponse
from app.schemas.summary_news import SummaryNewsResponse, SummaryNewsRequest

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends

from app.define import settings
from app.mq_main import celery_execute, redis
from app.schemas.crawl_news import QueueTimeHandle, QueueStatusHandle, QueueResult, QueueResponse

logger = logging.getLogger()
router = APIRouter()


@router.post(
    "/summary",
    # dependencies=[Depends(login_required)],
    response_model=DataResponse[QueueResponse]
)
def summary_news(request: SummaryNewsRequest) -> DataResponse:
    try:
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

        celery_execute.send_task(
            name="{}.{}".format(settings.AI_QUERY_NAME, settings.SUMMARY_NEWS_TASK),
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

    except Exception as e:
        logger.exception(e)