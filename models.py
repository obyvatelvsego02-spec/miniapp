from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from datetime import datetime
from db import Base


class ChatData(Base):
    __tablename__ = "chat_data"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, index=True)

    opening_balance = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    income = Column(Integer, default=0)
    fixed = Column(Integer, default=0)
    payouts = Column(Integer, default=0)
    manual_spread = Column(Integer, default=0)


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True)
    type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
