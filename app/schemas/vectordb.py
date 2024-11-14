import datetime
import json
from typing import Optional, Any

from pydantic import BaseModel, root_validator

class SaveVectorRequest(BaseModel):
    question: str
    query: str
    filter: dict
    class Config:
        schema_extra = {
            "example": {
                "request": "",
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

class SaveVectorResponse(BaseModel):
    collection_name: str
