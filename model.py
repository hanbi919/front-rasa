from typing import Optional

from pydantic import BaseModel, Field, field_validator


# 请求模型
class SendSmsV1Request(BaseModel):
    phone_numbers: str = Field(..., description="手机号，支持多个手机号用逗号分隔，最多50个")
    msg_id: Optional[str] = Field(None, description="短信ID")
    ext: Optional[str] = Field(None, description="扩展参数")

    @field_validator('phone_numbers')
    def validate_phone_numbers(cls, v):
        if not v:
            raise ValueError("手机号不能为空")
        phone_list = v.split(',')
        if len(phone_list) > 50:
            raise ValueError("手机号数量不能超过50个")
        return v


class SmsItem(BaseModel):
    phone: str = Field(..., description="手机号")
    info: Optional[str] = Field(None, description="短信内容")
    spnumber: Optional[str] = Field("", description="扩展码")
    msgid: Optional[str] = Field("", description="短信ID")

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v:
            raise ValueError("手机号不能为空")
        return v


# 响应模型
class ApiResponse(BaseModel):
    status: str = Field(..., description="状态：success或error")
    message: Optional[str] = Field("操作成功", description="错误信息")
    result: Optional[str] = Field(None, description="请求结果")
