from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta, timezone
from typing import Optional
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
from openai import OpenAI
import traceback

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
    questions = (
        db.query(models.QuestionModel)
        .filter(models.QuestionModel.id == question_id)
        .first()
    )
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
        .order_by(models.UserAnswerModel.id)
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


# Ollama APIクライアントの設定
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
)


# リクエストデータのモデル定義
class Question(BaseModel):
    tag: str
    is_correct: Optional[bool]  # None を許容
    time_taken: float


@app.post("/generate-feedback")
async def generate_feedback(request: Request):
    print("generate-feedbackにアクセスがあったよ。")
    try:
        data = await request.json()
        logging.debug(f"Received data: {data}")

        status = data.get("status", [])

        questions = [
            Question(
                tag=str(item["questionId"]),
                is_correct=item.get(
                    "isCorrect", False
                ),  # Noneの場合、デフォルト値としてFalseを設定
                time_taken=0,
            )
            for item in status
        ]
        print("questions:", questions)
        # questions = [
        #     Question(tag=str(item['questionId']), is_correct=item['isCorrect'], time_taken=0)
        #     for item in status
        # ]

        feedback_results = {
            "深層学習": generate_feedback_by_tag("1", questions),
            "法規・倫理": generate_feedback_by_tag("2", questions),
            "基礎数学": generate_feedback_by_tag("3", questions),
            "AI概論": generate_feedback_by_tag("4", questions),
            "機械学習": generate_feedback_by_tag("5", questions),
        }

        combined_feedback = "\n".join(
            f"{tag}: {text}" for tag, text in feedback_results.items()
        )
        return {"feedback": combined_feedback}

        # print(f"Generated feedback: {feedback_results}")
        # return feedback_results

    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(traceback.format_exc())  # トレースバックを追加
        raise HTTPException(status_code=500, detail="Internal Server Error")


# タグごとにフィードバックを生成する関数
def generate_feedback_by_tag(tag: str, data: List[Question]) -> str:
    # タグに関連付けられた問題の取得
    tagged_questions = [item for item in data if item.tag == tag]
    print("tagged_questions:", tagged_questions)

    if not tagged_questions:
        return f"{tag}に関連するデータがありません。"

    # correct_count = sum(item.is_correct for item in tagged_questions)
    # None を False 扱いにする
    correct_count = sum(
        1 if item.is_correct is True else 0 for item in tagged_questions
    )
    total_count = len(tagged_questions)
    avg_response_time = sum(item.time_taken for item in tagged_questions) / total_count
    print(
        "correct_count:",
        correct_count,
        "total_count:",
        total_count,
        "avg_response_time:",
        avg_response_time,
    )

    feedback = f"{tag}の正答率は{correct_count}/{total_count}で、平均解答時間は{avg_response_time:.2f}秒です。復習を行い、理解を深めましょう。\n"

    # フィードバックをOLLAMAに生成させる
    response = client.chat.completions.create(
        model="ELYZA",
        messages=[
            {
                "role": "system",
                "content": "あなたはAI検定の指導者で、受験者に役立つ日本語のフィードバックを提供します。フィードバックは簡潔で正確にし、不要な英語や冗長な情報は含めないでください。",
            },
            {"role": "user", "content": feedback},
        ],
    )

    # フィードバックの出力
    ollama_feedback = response.choices[0].message.content.strip()  # 不要な空白を削除
    return ollama_feedback


# アプリの起動
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


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
