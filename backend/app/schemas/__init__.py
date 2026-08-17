"""通用响应模型"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """统一响应封装"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None