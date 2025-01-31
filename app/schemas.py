from __future__ import annotations  # 追加
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List  # 修正済み


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# class UserTag(BaseModel):
#     id: int
#     tag: str

#     class Config:
#         orm_mode = True


class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class Question(BaseModel):
    id: int
    question_text: str
    correct_answer: str
    # choices: List[str]  # ここを修正
    choices: list[str]
    commentary: str
    tag: str | None = None

    class Config:
        orm_mode = True


class Session(BaseModel):
    id: int
    user_id: int
    token: str

    class Config:
        orm_mode = True


class SessionResponse(BaseModel):
    token: str


class FeedbackTemplate(BaseModel):
    id: int
    tag: str | None = None
    feedback: str

    class Config:
        orm_mode = True

class QuestionCreateChild(BaseModel):
    question_id: int = Field(description="問題ID")
    is_correct: Optional[bool] = Field(default=False, description="正解かどうか")  # デフォルト値を False に設定
    
class UserAnswer(BaseModel):
    id: int
    user_id: int
    question_id: int
    is_correct: bool
    quize_list_uuid: str
    answered_at: datetime

    class Config:
        orm_mode = True


class UserAnswerCreate(BaseModel):
    token: str = Field(description="トークン")
    child: list["QuestionCreateChild"] = Field(description="回答情報")


class UserAnswerDetailResponse(BaseModel):

    child: list["UserAnswerDetailResponseChild"]

    class Config:
        orm_mode = True


class UserAnswerDetailResponseChild(BaseModel):
    id: int
    user_id: int
    question_id: int
    question_text: str
    correct_answer: str
    choices: list[str]
    commentary: str
    tag: str | None = None
    # 　未回答Noneを追加
    is_correct: bool | None

    class Config:
        orm_mode = True


class UserAnswerResponse(BaseModel):
    child: list["UserAnswerResponseChild"]

    class Config:
        orm_mode = True


class UserAnswerResponseChild(BaseModel):
    quize_list_uuid: str
    answered_at: datetime

    class Config:
        orm_mode = True
