import logging
import re
from difflib import get_close_matches

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services import get_or_create, add_operation, clear_operations

BOT_TOKEN = "8748520635:AAFmBhQuFP-U31dDlwcHddpObPMzN27hqLI"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VALID_COMMANDS = ["приход", "фикс", "выдача"]
STRICT_RE = re.compile(r"^(приход|фикс|выдача)\s+(\d+)$", re.IGNORECASE)
LOOSE_RE = re.compile(r"^([а-яёa-z_\/]+)\s*(.*)$", re.IGNORECASE)


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

    if lower_text.startswith("/close_day"):
        db = None
        try:
            obj, db = get_or_create(msg.chat.id)

            summary_text = (
                "Итоги дня:\n"
                f"Баланс: {obj.balance}\n"
                f"Приход: {obj.income}\n"
                f"Фикс: {obj.fixed}\n"
                f"Выдачи: {obj.payouts}\n"
                f"Спред: {obj.income - obj.fixed}"
            )

            obj.opening_balance = obj.balance
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

    strict_match = STRICT_RE.match(lower_text)

    if strict_match:
        cmd, amount = strict_match.groups()
        amount = int(amount)

        db = None
        try:
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
            db.refresh(obj)

            await msg.answer(f"✅ Записано: {cmd} {amount}")

        except Exception:
            if db is not None:
                db.rollback()
            logger.exception("strict command failed")
            await msg.answer("Ошибка при сохранении операции")
        finally:
            if db is not None:
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
        return
