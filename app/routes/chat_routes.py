# app/routes/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chat import *
from app.services.ai_chat import generate_answer
from app.models.video import *
import time
from app.auth import get_current_user
from app.models.user import *
router = APIRouter()

@router.post("/ask/")
def ask_question(request: question, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token") 
    video = db.query(Video).filter(Video.url == request.url).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    retries = 0
    while not video.transcribed and retries < 10:
        time.sleep(1) 
        db.refresh(video)  
        retries += 1
        
    if not video.transcribed:
            return {"question": request.question, "answer": "Video transcription is not yet completed. Please try again later."}
    answer = generate_answer(request.question, video.transcribed)
    chat_entry = ChatHistory(
        user_id=current_user.id,
        url=video.url,
        question=request.question,
        answer=answer,
        transcribed=video.transcribed
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    return {"question": request.question, "answer": answer}

