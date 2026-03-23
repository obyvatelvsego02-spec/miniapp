from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import Update

from bot import bot, dp
from db import Base, engine
from services import get_or_create

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
        "spread": spread,
        "chat_title": f"Чат {chat_id}",
        "opening_balance": 0,
        "history": {
            "payouts": [],
            "income": [],
            "fixed": [],
        },
    }

    db.close()
    return result
