from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any, Generator, List
from app import models
from app.database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    Question,
    User,
    UserAnswer,
    UserAnswerCreate,
    UserCreate,
    UserLogin,
)

app = FastAPI()  # FastAPIインスタンスを作成


origins = [
    "http://localhost:5173",
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


@app.post("/login/")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.UserModel).filter(models.UserModel.email == user.email).first()
    )
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.password != user.password:
        raise HTTPException(status_code=404, detail="Password is incorrect")
    return db_user


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
    "/results/", response_model=UserAnswer, description="ユーザーの回答を登録する"
)
def post_result(data: UserAnswerCreate, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.UserAnswerModel)
        .filter(models.UserModel.id == data.user_id)
        .first()
    )
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    quize_list_uuid = uuid.uuid5()
    for question in data.child:
        new_question = models.UserAnswerModel(
            user_id=data.user_id,
            question_id=question.question_id,
            is_correct=question.is_correct,
            quize_list_uuid=quize_list_uuid,
            answered_at=datetime.datetime.now(),
        )
        db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


@app.get("/user_answers/{user_answer_id}", response_model=UserAnswer)
def read_user_answer(user_answer_id: int, user_id: int, db: Session = Depends(get_db)):
    user_answer = (
        db.query(models.UserAnswerModel)
        .filter(models.UserAnswerModel.user_id == user_id)
        .all()
    )
    if user_answer is None:
        raise HTTPException(status_code=404, detail="User answer not found")
    return user_answer


@app.get("/user_answers/{user_answer_id}", response_model=UserAnswer)
def read_user_answer(user_answer_id: int, user_id: int, db: Session = Depends(get_db)):
    user_answer = (
        db.query(models.UserAnswerModel)
        .filter(models.UserAnswerModel.user_id == user_id)
        .all()
    )
    if user_answer is None:
        raise HTTPException(status_code=404, detail="User answer not found")
    return user_answer
