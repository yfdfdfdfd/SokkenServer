from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), index=True)
    email = Column(String(64), unique=True, index=True)
    password = Column(String(64))


class QuestionModel(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_text = Column(String(255), nullable=False)
    correct_answer = Column(String(255), nullable=False)
    choices: JSON = Column(JSON, nullable=False)
    commentary = Column(Text, nullable=False)
    tag = Column(String(255), nullable=True)

    class Config:
        orm_mode = True


class FeedbackTemplateModel(Base):
    __tablename__ = "feedback_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String(255), nullable=True)
    feedback = Column(String(255), nullable=False)


class UserAnswerModel(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    quize_list_uuid: str = Column(String(255), nullable=False)
    answered_at = Column(DateTime, nullable=False)
