from sqlalchemy.exc import SQLAlchemyError

from db import SessionLocal
from models import ChatData, Operation


def get_or_create(chat_id):
    db = SessionLocal()
    try:
        obj = db.query(ChatData).filter_by(chat_id=chat_id).first()

        if not obj:
            obj = ChatData(
                chat_id=chat_id,
                opening_balance=0,
                balance=0,
                income=0,
                fixed=0,
                payouts=0,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)

        return obj, db

    except Exception:
        db.rollback()
        db.close()
        raise


def add_operation(db, chat_id, op_type, amount):
    try:
        op = Operation(
            chat_id=chat_id,
            type=op_type,
            amount=amount,
        )
        db.add(op)
        db.flush()
        return op
    except SQLAlchemyError:
        db.rollback()
        raise


def clear_operations(db, chat_id):
    try:
        db.query(Operation).filter_by(chat_id=chat_id).delete()
        db.flush()
    except SQLAlchemyError:
        db.rollback()
        raise


# 🔥 НОВОЕ: пересчёт данных по операциям
def recalculate_chat_data(db, chat_id: int):
    chat = db.query(ChatData).filter_by(chat_id=chat_id).first()
    if not chat:
        return None

    operations = (
        db.query(Operation)
        .filter_by(chat_id=chat_id)
        .order_by(Operation.created_at.asc())
        .all()
    )

    income = 0
    fixed = 0
    payouts = 0

    for op in operations:
        if op.type == "income":
            income += op.amount
        elif op.type == "fixed":
            fixed += op.amount
        elif op.type == "payouts":
            payouts += op.amount

    chat.income = income
    chat.fixed = fixed
    chat.payouts = payouts
    chat.balance = (chat.opening_balance or 0) + income - payouts

    db.flush()
    return chat


# 🔥 НОВОЕ: удаление операции + пересчёт
def delete_operation_and_recalculate(db, operation_id: int, chat_id: int):
    op = (
        db.query(Operation)
        .filter_by(id=operation_id, chat_id=chat_id)
        .first()
    )

    if not op:
        return None

    db.delete(op)
    db.flush()

    recalculate_chat_data(db, chat_id)
    db.commit()

    return True
