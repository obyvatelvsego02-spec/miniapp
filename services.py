from db import SessionLocal
from models import ChatData, Operation


def get_or_create(chat_id):
    db = SessionLocal()
    obj = db.query(ChatData).filter_by(chat_id=chat_id).first()

    if not obj:
        obj = ChatData(chat_id=chat_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)

    return obj, db


def add_operation(db, chat_id, op_type, amount):
    op = Operation(
        chat_id=chat_id,
        type=op_type,
        amount=amount,
    )
    db.add(op)
    
def clear_operations(db, chat_id):
    db.query(Operation).filter_by(chat_id=chat_id).delete()
