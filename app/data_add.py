from models import QuestionModel
from database import SessionLocal, engine

db = SessionLocal()
model = QuestionModel(
    question_text="次の(  )に当てはまる言葉を選択肢から１つ選べ\n\n学習等にデータを使用、他者と共有、又は、他者へデータを提供する場合にはデータが営業秘密等であるかに注意する必要がある。(   )のデータに対し、不正に取得されたものを使用する行為等が、不正競争防止法における民事上·刑事上の措置を受ける場合がある。でなくとも、ガイドライン等で一定の行為が禁止されているデータもある。例えば、金融分野における「機微(センシティブ)情報」等がある。",
    correct_answer="a.営業秘密·限定提供データ",
    choices=[
        "a.営業秘密·限定提供データ",
        "b.オープンデータ·営業秘密",
        "c.限定提供データ·学習データ",
        "d.オープンデータ·官民データ",
    ],
    tag="Data Usage",
)
db.add(model)
db.commit()
