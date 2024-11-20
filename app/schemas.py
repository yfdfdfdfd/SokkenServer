from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


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
    tag: str | None = None

    class Config:
        orm_mode = True


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
    is_correct: bool
    answered_at: datetime

    class Config:
        orm_mode = True
