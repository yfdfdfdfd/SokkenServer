from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any, Generator, List
from app import models, schemas
from app.database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

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


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
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


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.UserModel).offset(skip).limit(limit).all()
    return users


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
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
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
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


@app.get("/questions/{question_id}", response_model=schemas.Question)
def read_questions(question_id: int, db: Session = Depends(get_db)):
    questions = db.query(models.QuestionModel).offset(question_id).first()
    return questions
