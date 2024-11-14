import io
import os
from pathlib import Path

import json
from typing import Text, List, Union, Dict
from datetime import datetime

from loguru import logger

from app.mq_main import redis


class CeleryRedisClient(object):
    __instance = None

    @staticmethod
    def started(task_id: str, data: dict):
        data['status']['general_status'] = "SUCCESS"
        data['status']['task_status'] = "STARTED"
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)

    @staticmethod
    def failed(task_id: str, data: dict, err: dict):
        data['time']['end_generate'] = str(datetime.utcnow().timestamp())
        data['status']['task_status'] = "FAILED"
        data['error'] = err
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)

    @staticmethod
    def success(task_id: str, data: dict, response: dict):
        data['time']['end_generate'] = str(datetime.utcnow().timestamp())
        data['status']['task_status'] = "SUCCESS"
        data['task_result'] = response
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)
