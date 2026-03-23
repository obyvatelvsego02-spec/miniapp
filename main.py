import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import Update

from bot import bot, dp
from db import Base, engine
from models import Operation
from services import get_or_create

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

logger.info("MAIN.PY LOADED | version=debug-2026-03-24-01")


@app.get("/")
def root():
    logger.info("ROOT HIT")
    return {"ok": True}


@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        logger.info("WEBHOOK HIT | keys=%s", list(data.keys()))
        logger.info("WEBHOOK RAW UPDATE TYPE | has_message=%s", "message" in data)

        update = Update(**data)
        await dp.feed_update(bot, update)

        logger.info("WEBHOOK PROCESSED OK")
        return {"ok": True}
    except Exception:
        logger.exception("WEBHOOK FAILED")
        return {"ok": False}


@app.get("/api/dashboard/{chat_id}")
def dashboard(chat_id: int):
    logger.info("DASHBOARD HIT | chat_id=%s", chat_id)

    obj, db = get_or_create(chat_id)
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
            "amount": op.amount,
            "at": op.created_at.strftime("%d.%m %H:%M"),
        }

        if op.type == "income":
            history["income"].append(item)
        elif op.type == "fixed":
            history["fixed"].append(item)
        elif op.type == "payouts":
            history["payouts"].append(item)

    result = {
        "balance": obj.balance,
        "income": obj.income,
        "fixed": obj.fixed,
        "payouts": obj.payouts,
        "spread": spread,
        "chat_title": f"Чат {chat_id}",
        "opening_balance": 0,
        "history": history,
    }

    db.close()
    logger.info("DASHBOARD OK | chat_id=%s", chat_id)
    return result
