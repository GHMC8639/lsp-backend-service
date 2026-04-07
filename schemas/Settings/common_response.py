from pydantic import BaseModel
from typing import Any


class CommonResponse(BaseModel):
    success: bool
    message: str
    data: Any = None