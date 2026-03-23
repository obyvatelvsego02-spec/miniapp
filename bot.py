import re
from difflib import get_close_matches

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services import get_or_create, add_operation

BOT_TOKEN = "8748520635:AAFmBhQuFP-U31dDlwcHddpObPMzN27hqLI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VALID_COMMANDS = ["приход", "фикс", "выдача"]

STRICT_RE = re.compile(r"^(приход|фикс|выдача)\s+(\d+)$", re.IGNORECASE)
LOOSE_RE = re.compile(r"^([а-яёa-z]+)\s*(.*)$", re.IGNORECASE)


def closest_command(word: str):
    matches = get_close_matches(word.lower(), VALID_COMMANDS, n=1, cutoff=0.7)
    return matches[0] if matches else None


@dp.message()
async def handle(msg: types.Message):
    if not msg.text:
        return

    text = msg.text.strip()
    lower_text = text.lower()

    if lower_text.startswith("/dashboard"):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть дашборд",
                        url=f"https://t.me/OnyxKent_bot/dashboard?startapp=group_{msg.chat.id}",
                    )
                ]
            ]
        )
        await msg.answer("Открой дашборд:", reply_markup=kb)
        return

    strict_match = STRICT_RE.match(lower_text)
    if strict_match:
        cmd, amount = strict_match.groups()
        amount = int(amount)

        obj, db = get_or_create(msg.chat.id)

        if cmd == "приход":
    obj.balance += amount
    obj.income += amount
    add_operation(db, msg.chat.id, "income", amount)

elif cmd == "фикс":
    obj.fixed += amount
    add_operation(db, msg.chat.id, "fixed", amount)

elif cmd == "выдача":
    obj.balance -= amount
    obj.payouts += amount
    add_operation(db, msg.chat.id, "payouts", amount)

db.commit()
db.close()
return

    loose_match = LOOSE_RE.match(lower_text)
    if not loose_match:
        return

    maybe_cmd, rest = loose_match.groups()
    suggestion = closest_command(maybe_cmd)

    if suggestion and maybe_cmd not in VALID_COMMANDS:
        if rest.strip().isdigit():
            await msg.answer(
                f"❌ Похоже, команда написана с ошибкой.\n"
                f"Попробуй так: `{suggestion} {rest.strip()}`",
                parse_mode="Markdown",
            )
        else:
            await msg.answer(
                "❌ Неверный формат.\n"
                "Используй:\n"
                "`приход 100`\n"
                "`фикс 50`\n"
                "`выдача 20`",
                parse_mode="Markdown",
            )
