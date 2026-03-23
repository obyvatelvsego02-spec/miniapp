from fastapi import FastAPI, Request
from aiogram.types import Update

from bot import bot, dp
from db import Base, engine
from services import get_or_create

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/api/dashboard/{chat_id}")
def dashboard(chat_id: int):
    obj, db = get_or_create(chat_id)

    spread = obj.income - obj.fixed

    result = {
        "balance": obj.balance,
        "income": obj.income,
        "fixed": obj.fixed,
        "payouts": obj.payouts,
        "spread": spread
    }

    db.close()
    return result