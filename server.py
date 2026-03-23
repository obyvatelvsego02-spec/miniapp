import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "finance_state.json"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Finance Mini App")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def load_db() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"chats": {}}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/chat/{chat_id}")
def get_chat(chat_id: str) -> dict:
    db = load_db()
    state = db.get("chats", {}).get(str(chat_id))
    if not state:
        raise HTTPException(status_code=404, detail="chat not found")
    balance = state["opening_balance"] + state["income"] - state["payouts"]
    spread = state["income"] - state["fixed"]
    history = state.get("history", {})
    return {
        "chat_id": state["chat_id"],
        "chat_title": state.get("chat_title", f"Chat {chat_id}"),
        "opening_balance": state["opening_balance"],
        "balance": balance,
        "spread": spread,
        "income": state["income"],
        "fixed": state["fixed"],
        "payouts": state["payouts"],
        "history": history,
    }
