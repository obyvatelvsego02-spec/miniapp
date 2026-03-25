import logging
import re
from difflib import get_close_matches

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services import get_or_create, add_operation, clear_operations

BOT_TOKEN = "8748520635:AAFmBhQuFP-U31dDlwcHddpObPMzN27hqLI"
BOT_USERNAME = "OnyxKent_bot"
BOT_APP_SHORT_NAME = "dashboard"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VALID_COMMANDS = ["приход", "фикс", "выдача", "спред"]

STRICT_RE = re.compile(
    r"^(приход|фикс|выдача|спред)\s+(\d+(?:[.,]\d+)?)$",
    re.IGNORECASE
)

LOOSE_RE = re.compile(
    r"^(\S+)\s+(\d+(?:[.,]\d+)?)$",
    re.IGNORECASE
)

CYR_RE = re.compile(r"^[А-Яа-яЁё]+$")


def closest_command(word: str):
    matches = get_close_matches(word.lower(), VALID_COMMANDS, n=1, cutoff=0.7)
    return matches[0] if matches else None


def amount_value(raw: str) -> float:
    return float(raw.replace(",", "."))


@dp.message()
async def handle(msg: types.Message):
    if not msg.text:
        return

    text = msg.text.strip()
    lower_text = text.lower()

    # /dashboard
    if lower_text.startswith("/dashboard"):
        payload = f"group_{msg.chat.id}"
        url = f"https://t.me/{BOT_USERNAME}/{BOT_APP_SHORT_NAME}?startapp={payload}"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть дашборд", url=url)]
            ]
        )
        await msg.answer("📊 Дашборд группы", reply_markup=kb)
        return

    # /close_day
    if lower_text.startswith("/close_day"):
        db = None
        try:
            obj, db = get_or_create(msg.chat.id)

            day_balance = obj.income - obj.payouts

            summary_text = (
                "📊 Сводка за день\n\n"
                f"Приход: {obj.income}\n"
                f"Фикс: {obj.fixed}\n"
                f"Выдачи: {obj.payouts}\n"
                f"Спред: {obj.income - obj.fixed}\n\n"
                f"💰 Баланс дня: {day_balance}"
            )

            obj.opening_balance = day_balance
            obj.balance = day_balance
            obj.income = 0
            obj.fixed = 0
            obj.payouts = 0

            clear_operations(db, msg.chat.id)
            db.commit()

            await msg.answer(summary_text)

        except Exception:
            if db is not None:
                db.rollback()
            logger.exception("close_day failed")
            await msg.answer("Ошибка при закрытии дня")
        finally:
            if db is not None:
                db.close()
        return

    # /reset_chat
    if lower_text.startswith("/reset_chat"):
        db = None
        try:
            obj, db = get_or_create(msg.chat.id)

            obj.opening_balance = 0
            obj.balance = 0
            obj.income = 0
            obj.fixed = 0
            obj.payouts = 0

            clear_operations(db, msg.chat.id)
            db.commit()

            await msg.answer("♻️ Чат полностью обнулён")

        except Exception:
            if db is not None:
                db.rollback()
            logger.exception("reset_chat failed")
            await msg.answer("Ошибка при сбросе чата")
        finally:
            if db is not None:
                db.close()
        return

    # Строгая команда: приход 100 / фикс 50 / выдача 20
    strict = STRICT_RE.fullmatch(text)
    if strict:
        command = strict.group(1).lower()
        value = amount_value(strict.group(2))

        db = None
        try:
            obj, db = get_or_create(msg.chat.id)

            if command == "приход":
                obj.balance += value
                obj.income += value
                add_operation(db, msg.chat.id, "income", value)

            elif command == "фикс":
                obj.fixed += value
                add_operation(db, msg.chat.id, "fixed", value)

            elif command == "выдача":
                obj.balance -= value
                obj.payouts += value
                add_operation(db, msg.chat.id, "payouts", value)

            db.commit()

        except Exception:
            if db is not None:
                db.rollback()
            logger.exception("strict command failed")
        finally:
            if db is not None:
                db.close()

        return

    # Похожая команда с опечаткой: фис 100 / выдча 50
    loose = LOOSE_RE.fullmatch(text)
    if not loose:
        return

    first_word = loose.group(1)
    amount = loose.group(2)

    # Если это не кириллица — молчим
    if not CYR_RE.fullmatch(first_word):
        return

    suggestion = closest_command(first_word)

    if suggestion and suggestion != first_word.lower():
        await msg.answer(
            f"Ошибка в сообщении\n"
            f"Похоже, вы имели в виду: {suggestion} {amount}"
        )
        return

    return
