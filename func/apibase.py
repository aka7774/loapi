import time

from pydantic import BaseModel, Field

class ApiResponse(BaseModel):
   status: int = Field(description="ステータス")
   servertime: float = Field(description="サーバー時刻")
   result: str = Field(description="結果")
   detail: dict = Field(description="詳細")

def res(status = 0, result = '', detail = {}):
    return {
        "status": status,
        "servertime": time.time(),
        "result": result,
        "detail": detail,
    }
