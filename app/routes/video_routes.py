# app/routes/video_routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.video import *
from app.models.user import *
from app.services.video_service import process_video
from app.auth import get_current_user
router = APIRouter()

@router.post("/videos/")
def create_video(
    video: VideoCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token") 
    user_id=current_user.id
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db_video = Video(url=video.url, transcribed="", user_id=user_id)
    db.add(db_video)
    db.commit()
    #db.refresh(db_video)
    background_tasks.add_task(process_video, video.url, user_id, db_video.id)
    return {"task_id": db_video.id, "status": "processing", "video_id": db_video.id}