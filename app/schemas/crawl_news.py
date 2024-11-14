import datetime
import json
from typing import Optional, Any

from pydantic import BaseModel


class QueueTimeHandle(BaseModel):
    start_generate: str = None
    end_generate: str = None


class QueueStatusHandle(BaseModel):
    general_status: str = "PENDING"
    task_status: str = None


class QueueResult(BaseModel):
    task_id: str
    status: dict = None
    time: dict = None
    task_result: Any = None
    error: Optional[Any] = None


class QueueResponse(BaseModel):
    status: str = "PENDING"
    time: datetime.datetime
    task_id: str

class CrawlNewsRequest(BaseModel):
    url: str
    class Config:
        schema_extra = {
            "example": {
                "url": "https://edition.cnn.com",
            }
        }
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
