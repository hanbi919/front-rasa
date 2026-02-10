from fastapi import Request, HTTPException

from util import getConfig


# 鉴权
def verify_token(request: Request):
    token = request.headers.get("X-Access-Token")
    if not token:
        raise HTTPException(status_code=401, detail={"status": "error", "message": "鉴权失败: 请求头缺少TOKEN"})
    if token != getConfig()["TOKEN"]:
        raise HTTPException(status_code=401, detail={"status": "error", "message": "鉴权失败: TOKEN不匹配"})
    return token
