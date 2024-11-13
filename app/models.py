from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), index=True)
    email = Column(String(64), unique=True, index=True)
    password = Column(String(64))


class ProblemModel(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(64), index=True)
    statement = Column(String(256))
    option_a = Column(String(64))
    option_b = Column(String(64))
    option_c = Column(String(64))
    option_d = Column(String(64))
    correct_option = Column(String(1))
    flag = Column(Integer, default=False)
