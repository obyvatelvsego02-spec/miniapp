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
