import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import Update

from bot import bot, dp
from db import Base, engine
from models import Operation
from services import delete_operation_and_recalculate, get_or_create

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://miniapp-phi-umber.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"ok": True}


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    logger.info("WEBHOOK HIT | keys=%s", list(data.keys()))
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


# 🔹 ДАШБОРД
@app.get("/api/dashboard/{chat_id}")
def dashboard(chat_id: int):
    obj, db = get_or_create(chat_id)
    try:
        spread = obj.income - obj.fixed

        operations = (
            db.query(Operation)
            .filter_by(chat_id=chat_id)
            .order_by(Operation.created_at.desc())
            .all()
        )

        history = {
            "payouts": [],
            "income": [],
            "fixed": [],
        }

        for op in operations:
            item = {
                "id": op.id,  # 🔥 добавили id
                "amount": op.amount,
                "at": op.created_at.strftime("%d.%m %H:%M"),
            }

            if op.type == "income":
                history["income"].append(item)
            elif op.type == "fixed":
                history["fixed"].append(item)
            elif op.type == "payouts":
                history["payouts"].append(item)

        return {
            "balance": obj.balance,
            "income": obj.income,
            "fixed": obj.fixed,
            "payouts": obj.payouts,
            "spread": spread,
            "manual_spread": obj.manual_spread or 0,
            "cap_amount": obj.cap_amount or 0,
            "chat_title": f"Чат {chat_id}",
            "opening_balance": obj.opening_balance or 0,
            "history": history,
        }

    finally:
        db.close()


# 🔹 DEBUG (оставляем как есть)
@app.get("/api/debug/{chat_id}")
def debug_chat(chat_id: int):
    obj, db = get_or_create(chat_id)
    try:
        operations = (
            db.query(Operation)
            .filter_by(chat_id=chat_id)
            .order_by(Operation.created_at.desc())
            .all()
        )

        return {
            "chat_id": chat_id,
            "chat_data": {
                "opening_balance": obj.opening_balance,
                "balance": obj.balance,
                "income": obj.income,
                "fixed": obj.fixed,
                "payouts": obj.payouts,
            },
            "operations_count": len(operations),
            "operations": [
                {
                    "id": op.id,
                    "type": op.type,
                    "amount": op.amount,
                    "created_at": op.created_at.isoformat() if op.created_at else None,
                }
                for op in operations[:20]
            ],
        }
    finally:
        db.close()


# 🔥 УДАЛЕНИЕ ОПЕРАЦИИ
@app.post("/api/operation/delete/{operation_id}")
def delete_operation(operation_id: int, chat_id: int):
    obj, db = get_or_create(chat_id)

    try:
        result = delete_operation_and_recalculate(db, operation_id, chat_id)

        if not result:
            return {"ok": False, "error": "operation not found"}

        spread = obj.income - obj.fixed

        operations = (
            db.query(Operation)
            .filter_by(chat_id=chat_id)
            .order_by(Operation.created_at.desc())
            .all()
        )

        history = {
            "payouts": [],
            "income": [],
            "fixed": [],
        }

        for op in operations:
            item = {
                "id": op.id,
                "amount": op.amount,
                "at": op.created_at.strftime("%d.%m %H:%M"),
            }

            if op.type == "income":
                history["income"].append(item)
            elif op.type == "fixed":
                history["fixed"].append(item)
            elif op.type == "payouts":
                history["payouts"].append(item)

        return {
            "ok": True,
            "balance": obj.balance,
            "income": obj.income,
            "fixed": obj.fixed,
            "payouts": obj.payouts,
            "spread": spread,
            "history": history,
        }

    finally:
        db.close()
