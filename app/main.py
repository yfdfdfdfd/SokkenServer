from datetime import datetime, timedelta, timezone
import uuid
from fastapi import Cookie, FastAPI, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from typing import Any, Generator, List
from app import models
from app.database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    Question,
    SessionResponse,
    User,
    UserAnswer,
    UserAnswerCreate,
    UserAnswerDetailResponse,
    UserAnswerDetailResponseChild,
    UserAnswerResponse,
    UserAnswerResponseChild,
    UserCreate,
    UserLogin,
)
import logging

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI()  # FastAPIインスタンスを作成


origins = [
    "http://localhost:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)


# データベースのセッションを取得
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.UserModel).filter(models.UserModel.email == user.email).first()
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.UserModel(
        name=user.name, email=user.email, password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.UserModel).offset(skip).limit(limit).all()
    return users


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}


# レスポンスモデルはreturnモデルと同じものを使う
@app.post("/login/", response_model=SessionResponse)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.UserModel).filter(models.UserModel.email == user.email).first()
    )
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.password != user.password:
        raise HTTPException(status_code=404, detail="Password is incorrect")
    token = uuid.uuid4().hex
    new_session = models.UserSessionModel(user_id=db_user.id, token=token)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse(token=token)


@app.post("/login/{user_id}/reset_password")
def reset_password(user_id: int, new_password: str, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.password = new_password
    db.commit()
    db.refresh(db_user)
    return {"message": "Password reset successfully"}


@app.get("/questions/{question_id}", response_model=Question)
def read_questions(question_id: int, db: Session = Depends(get_db)):
    questions = db.query(models.QuestionModel).offset(question_id).first()
    return questions


@app.post(
    "/results/",
    description="ユーザーの回答を送信する",
)
def post_result(data: UserAnswerCreate, db: Session = Depends(get_db)):
    db_session = db.query(models.UserSessionModel).filter(
        models.UserSessionModel.token == data.token
    )
    session = db_session.first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    db_user = (
        db.query(models.UserModel)
        .filter(models.UserModel.id == session.user_id)
        .first()
    )
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    quize_list_uuid = str(uuid.uuid4())
    for question in data.child:
        new_question = models.UserAnswerModel(
            user_id=session.user_id,
            question_id=question.question_id,
            is_correct=question.is_correct,
            quize_list_uuid=quize_list_uuid,
            answered_at=datetime.now(),
        )
        db.add(new_question)
        db.flush()
    db.commit()
    db.refresh(new_question)


# --日付の表示だけのと詳細表示（問題一問一問の表示）のページでAPIを分ける-- #


@app.get("/user_history_uuid", response_model=UserAnswerResponse)
def read_user_answer(token: str, db: Session = Depends(get_db)):
    session = (
        db.query(models.UserSessionModel)
        .filter(models.UserSessionModel.token == token)
        .first()
    )

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_answer = (
        db.query(
            models.UserAnswerModel.quize_list_uuid, models.UserAnswerModel.answered_at
        )
        .filter(models.UserAnswerModel.user_id == session.user_id)
        .distinct()
    )
    if user_answer is None:
        raise HTTPException(status_code=404, detail="User answer not found")

    # モデルからスキーマに変換
    child = []
    for answer in user_answer:
        child.append(
            UserAnswerResponseChild(
                quize_list_uuid=answer.quize_list_uuid,
                answered_at=answer.answered_at,
            )
        )
    return UserAnswerResponse(child=child)


# quize_list_uuidを使って問題を分けて表示する
@app.get("/user_history_by_uuid/", response_model=UserAnswerDetailResponse)
def read_user_answer(quize_list_uuid: str, token: str, db: Session = Depends(get_db)):
    session = (
        db.query(models.UserSessionModel)
        .filter(models.UserSessionModel.token == token)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_answers = (
        db.query(models.UserAnswerModel, models.QuestionModel)
        .join(
            models.QuestionModel,
            models.UserAnswerModel.question_id == models.QuestionModel.id,
        )
        .filter(models.UserAnswerModel.quize_list_uuid == quize_list_uuid)
        .all()
    )
    if user_answers is None:
        raise HTTPException(status_code=404, detail="User answer not found")

    # print(user_answers)
    # print(quize_list_uuid)

    # モデルからスキーマに変換
    child = []
    for answer, question in user_answers:
        # UserAnswerDetailResponseChildの右辺がanyにならないように
        assert isinstance(answer, models.UserAnswerModel)
        assert isinstance(question, models.QuestionModel)
        # print(answer.id)

        child.append(
            UserAnswerDetailResponseChild(
                id=answer.id,
                user_id=answer.user_id,
                question_id=answer.question_id,
                question_text=question.question_text,
                correct_answer=question.correct_answer,
                choices=question.choices,
                commentary=question.commentary,
                tag=question.tag,
                is_correct=answer.is_correct,
                quize_list_uuid=answer.quize_list_uuid,
                answered_at=answer.answered_at,
            )
        )
    return UserAnswerDetailResponse(child=child)


@app.delete("/user_history_uuid")
def delete_user_answer(token: str, quize_list_uuid: str, db: Session = Depends(get_db)):
    session = (
        db.query(models.UserSessionModel)
        .filter(models.UserSessionModel.token == token)
        .first()
    )

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    db.query(models.UserAnswerModel).filter(
        models.UserAnswerModel.user_id == session.user_id,
        models.UserAnswerModel.quize_list_uuid == quize_list_uuid,
    ).delete()
    db.commit()
