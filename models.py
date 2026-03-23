from sqlalchemy import Column, Integer, BigInteger
from db import Base

class ChatData(Base):
    __tablename__ = "chat_data"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, index=True)

    balance = Column(Integer, default=0)
    income = Column(Integer, default=0)
    fixed = Column(Integer, default=0)
    payouts = Column(Integer, default=0)