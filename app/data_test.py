from models import QuestionModel

from database import SessionLocal, engine

db = SessionLocal()
model = QuestionModel(
    question_text="ディープラーニングとニューラルネットワークに関する以下のアからエまでの記述のうち、最も適切ではないものを１つ選びなさい。",
    correct_answer="エ．	ディープラーニングでは、学習対象となる変数（特徴量）を定義して入力する必要がある。",
    choices=[
        "ア．	ディープラーニングは、画像認識、音声認識などの精度が格段に向上するなどの成果をもたらし、AI技術の発達に大きな影響を与えている。",
        "イ．	ニューラルネットワークは入力層、中間層（隠れ層）、出力層の３層から成り立っている。",
        "ウ．	ニューラルネットワークのうち、中間層（隠れ層）が複数の層となっているものを用いるのがディープラーニングである。",
        "エ．	ディープラーニングでは、学習対象となる変数（特徴量）を定義して入力する必要がある。",
    ],
    tag="IT",
)
db.add(model)
db.commit()
