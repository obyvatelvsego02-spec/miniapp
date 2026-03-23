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

logger.info("BOT.PY LOADED | version=debug-2026-03-24-01")


def closest_command(word: str):
    matches = get_close_matches(word.lower(), VALID_COMMANDS, n=1, cutoff=0.7)
    return matches[0] if matches else None


@dp.message()
async def handle(msg: types.Message):
    logger.info(
        "HANDLE START | chat_id=%s | text=%r | content_type=%s",
        msg.chat.id if msg.chat else None,
        msg.text,
        getattr(msg, "content_type", None),
    )

    if not msg.text:
        logger.info("SKIP: no text")
        return

    text = msg.text.strip()
    lower_text = text.lower()

    logger.info("TEXT PARSED | original=%r | lower=%r", text, lower_text)

    if lower_text.startswith("/dashboard"):
        logger.info("COMMAND: /dashboard")
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
        logger.info("DASHBOARD SENT")
        return

    if lower_text.startswith("/close_day"):
        logger.info("COMMAND: /close_day")
        db = None
        try:
            obj, db = get_or_create(msg.chat.id)
            logger.info(
                "BEFORE CLOSE_DAY | balance=%s income=%s fixed=%s payouts=%s",
                obj.balance,
                obj.income,
                obj.fixed,
                obj.payouts,
            )

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
            logger.info("ABOUT TO COMMIT /close_day")
            db.commit()
            logger.info("COMMIT OK /close_day")

            await msg.answer(summary_text)
            logger.info("ANSWER SENT /close_day")
        except Exception:
            logger.exception("ERROR IN /close_day")
            if db is not None:
                db.rollback()
            await msg.answer("Ошибка при закрытии дня. Смотри Railway logs.")
        finally:
            if db is not None:
                db.close()
        return

    if lower_text.startswith("/reset_chat"):
        logger.info("COMMAND: /reset_chat")
        db = None
        try:
            obj, db = get_or_create(msg.chat.id)
            obj.opening_balance = 0
            obj.balance = 0
            obj.income = 0
            obj.fixed = 0
            obj.payouts = 0

            clear_operations(db, msg.chat.id)
            logger.info("ABOUT TO COMMIT /reset_chat")
            db.commit()
            logger.info("COMMIT OK /reset_chat")

            await msg.answer("♻️ Чат полностью обнулён")
            logger.info("ANSWER SENT /reset_chat")
        except Exception:
            logger.exception("ERROR IN /reset_chat")
            if db is not None:
                db.rollback()
            await msg.answer("Ошибка при сбросе чата. Смотри Railway logs.")
        finally:
            if db is not None:
                db.close()
        return

    strict_match = STRICT_RE.match(lower_text)
    logger.info("STRICT MATCH RESULT | matched=%s", bool(strict_match))

    if strict_match:
        cmd, amount = strict_match.groups()
        amount = int(amount)

        logger.info("STRICT COMMAND ACCEPTED | cmd=%s | amount=%s", cmd, amount)

        db = None
        try:
            obj, db = get_or_create(msg.chat.id)

            logger.info(
                "DB BEFORE | balance=%s income=%s fixed=%s payouts=%s",
                obj.balance,
                obj.income,
                obj.fixed,
                obj.payouts,
            )

            if cmd == "приход":
                obj.balance += amount
                obj.income += amount
                add_operation(db, msg.chat.id, "income", amount)
                logger.info("APPLIED income")
            elif cmd == "фикс":
                obj.fixed += amount
                add_operation(db, msg.chat.id, "fixed", amount)
                logger.info("APPLIED fixed")
            elif cmd == "выдача":
                obj.balance -= amount
                obj.payouts += amount
                add_operation(db, msg.chat.id, "payouts", amount)
                logger.info("APPLIED payouts")

            logger.info(
                "DB AFTER CHANGE BEFORE COMMIT | balance=%s income=%s fixed=%s payouts=%s",
                obj.balance,
                obj.income,
                obj.fixed,
                obj.payouts,
            )

            logger.info("ABOUT TO COMMIT strict command")
            db.commit()
            logger.info("COMMIT OK strict command")

            await msg.answer(f"✅ Записано: {cmd} {amount}")
            logger.info("ANSWER SENT strict command")

        except Exception:
            logger.exception("ERROR IN STRICT COMMAND")
            if db is not None:
                db.rollback()
            await msg.answer("Ошибка при сохранении операции. Смотри Railway logs.")
        finally:
            if db is not None:
                db.close()
        return

    loose_match = LOOSE_RE.match(lower_text)
    logger.info("LOOSE MATCH RESULT | matched=%s", bool(loose_match))

    if not loose_match:
        logger.info("SKIP: loose_match is empty")
        return

    maybe_cmd, rest = loose_match.groups()
    logger.info("LOOSE PARSED | maybe_cmd=%r | rest=%r", maybe_cmd, rest)

    suggestion = closest_command(maybe_cmd)

    if suggestion and maybe_cmd not in VALID_COMMANDS:
        if rest.strip().isdigit():
            logger.info("TYPO SUGGESTION | suggestion=%s", suggestion)
            await msg.answer(
                f"❌ Похоже, команда написана с ошибкой.\n"
                f"Попробуй так: `{suggestion} {rest.strip()}`",
                parse_mode="Markdown",
            )
        else:
            logger.info("BAD FORMAT")
            await msg.answer(
                "❌ Неверный формат.\n"
                "Используй:\n"
                "`приход 100`\n"
                "`фикс 50`\n"
                "`выдача 20`",
                parse_mode="Markdown",
            )
        return

    logger.info("IGNORED MESSAGE | text=%r", lower_text)
