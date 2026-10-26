from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chatbot import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
)
from app.services.chatbot import (
    create_chat_feedback,
    create_guest_session,
    process_chat_message,
)


router = APIRouter(prefix="/chat", tags=["Chatbot"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
)
def create_chat_session(db: Session = Depends(get_db)):
    session, token = create_guest_session(db)

    return {
        "session_id": session.id,
        "guest_token": token,
    }


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
)
def send_chat_message(
    session_id: int,
    payload: ChatMessageRequest,
    x_chat_token: str = Header(),
    db: Session = Depends(get_db),
):
    return process_chat_message(
        db=db,
        session_id=session_id,
        token=x_chat_token,
        message=payload.message,
    )

@router.post(
    "/sessions/{session_id}/feedback",
    response_model=ChatFeedbackResponse,
)
def submit_chat_feedback(
    session_id: int,
    payload: ChatFeedbackRequest,
    x_chat_token: str = Header(),
    db: Session = Depends(get_db),
):
    return create_chat_feedback(
        db=db,
        session_id=session_id,
        token=x_chat_token,
        rating=payload.rating,
        message_id=payload.message_id,
        comments=payload.comments,
    )