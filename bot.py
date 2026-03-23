from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import Bot, Dispatcher, types
import re
from services import get_or_create

BOT_TOKEN = "8748520635:AAFmBhQuFP-U31dDlwcHddpObPMzN27hqLI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle(msg: types.Message):
    if not msg.text:
        return

    text = msg.text.lower().strip()

    match = re.match(r"^(приход|фикс|выдача)\s+(\d+)$", text)
    if not match:
        return

    cmd, amount = match.groups()
    amount = int(amount)

    obj, db = get_or_create(msg.chat.id)

    if cmd == "приход":
        obj.balance += amount
        obj.income += amount

    elif cmd == "фикс":
        obj.fixed += amount

    elif cmd == "выдача":
        obj.balance -= amount
        obj.payouts += amount

    db.commit()
    db.close()
    await msg.answer(f"OK chat_id={msg.chat.id} | {cmd} {amount}")

@dp.message(commands=["dashboard"])
async def dashboard(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Открыть дашборд",
            web_app=WebAppInfo(
                url=f"https://miniapp-production-2f44.up.railway.app/?startapp=group_{msg.chat.id}"
            )
        )]
    ])
    await msg.answer("Открой дашборд:", reply_markup=kb)
