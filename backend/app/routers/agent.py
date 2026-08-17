"""智能问数 Agent API（CURVE_CHAT）"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..services import CurveChatService

router = APIRouter(prefix="/api/agent", tags=["智能问数"])


@router.post("/chat", response_model=ResponseBase)
def chat(
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """智能问数：自然语言查询曲线数据"""
    query = payload.get("query", "")
    session_id = payload.get("session_id")
    if not query:
        return ResponseBase(code=400, message="query 不能为空")

    svc = CurveChatService(db)
    res = svc.chat(
        user_query=query,
        session_id=session_id,
        user_id=str(user.get("id", "")),
    )
    return ResponseBase(data=res)


@router.get("/sessions", response_model=ResponseBase)
def list_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """会话列表（按 session 聚合）"""
    from sqlalchemy import func
    from ..models import CurvSmartDialogue

    rows = (
        db.query(
            CurvSmartDialogue.session_id,
            func.max(CurvSmartDialogue.created_at).label("last_time"),
        )
        .filter(CurvSmartDialogue.user_id == str(user.get("id", "")))
        .group_by(CurvSmartDialogue.session_id)
        .order_by(func.max(CurvSmartDialogue.created_at).desc())
        .limit(limit)
        .all()
    )
    return ResponseBase(data=[
        {"session_id": r.session_id, "last_time": r.last_time.isoformat() if r.last_time else None}
        for r in rows
    ])