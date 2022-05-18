from pydantic import BaseModel
from typing import Any
from enum import Enum
from fastapi import status


class Status(str, Enum):
    success = "success"
    failed = "failed"


class Error(BaseModel):
    type: str
    code: int
    message: str


class ApiException(Exception):
    status_code: int
    error: Error

    def __init__(self, status_code, error: Error):
        super().__init__(status_code)
        self.status_code = status_code
        self.error = error


class ApiResponse(BaseModel):
    status: Status
    errors: list[Error] | None = None
    data: dict[str, Any] | BaseModel | None = None

    class Config:
        use_enum_values = True