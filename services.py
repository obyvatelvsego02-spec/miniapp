from db import SessionLocal
from models import ChatData

def get_or_create(chat_id):
    db = SessionLocal()
    obj = db.query(ChatData).filter_by(chat_id=chat_id).first()

    if not obj:
        obj = ChatData(chat_id=chat_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)

    return obj, db