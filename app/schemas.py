from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


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


class UserAnswer(BaseModel):
    id: int
    user_id: int
    question_id: int
    commentary: str
    is_correct: bool
    quize_list_uuid: str
    answered_at: datetime

    class Config:
        orm_mode = True


class UserAnswerCreate(BaseModel):
    token: str = Field(description="トークン")
    child: list["QuestionCreateChild"] = Field(description="回答情報")


class QuestionCreateChild(BaseModel):
    question_id: int
    commentary: str
    is_correct: Optional[bool] = Field(description="正解かどうか")
