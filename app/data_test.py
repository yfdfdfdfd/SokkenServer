from models import QuestionModel

from database import SessionLocal, engine

db = SessionLocal()
model = QuestionModel(
    question_text="What is the capital of France?",
    correct_answer="Paris",
    choices=["Berlin", "Madrid", "Paris", "Rome"],
    tag="geography",
)
db.add(model)
db.commit()
