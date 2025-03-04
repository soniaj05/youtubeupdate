# app/services/video_service.py
import os
import yt_dlp as youtube_dl
import whisper
from fastapi import HTTPException
import logging
from app.database import get_db
from app.models.video import Video

logger = logging.getLogger(__name__)
model = whisper.load_model("base")

def extract_audio(url: str) -> str:
    tmp_folder = "tmp"
    os.makedirs(tmp_folder, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(tmp_folder, '%(id)s.%(ext)s'),
        'quiet': False,
        'verbose': True,
        'keepvideo': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            temp_filename = ydl.prepare_filename(info_dict)
            audio_filename = temp_filename.replace('.webm', '.m4a')
            logger.info(f"Downloaded file: {audio_filename}")
            logger.info(f"File size: {os.path.getsize(audio_filename)} bytes")
            if not os.path.exists(audio_filename) or os.path.getsize(audio_filename) == 0:
                logger.error("Downloaded file is missing or empty")
                raise HTTPException(status_code=400, detail="Downloaded file is missing or empty")
            return audio_filename
    except Exception as e:
        logger.error(f"Failed to extract audio: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to extract audio: {str(e)}")

def transcribe_audio(audio_filename: str) -> str:
    try:
        if not os.path.exists(audio_filename) or os.path.getsize(audio_filename) == 0:
            logger.error("Audio file is empty or missing before transcription.")
            raise HTTPException(status_code=400, detail="Audio file is empty or missing before transcription.")
        
        logger.info(f"Transcribing file: {audio_filename}, Size: {os.path.getsize(audio_filename)} bytes")
        result = model.transcribe(audio_filename)
        logger.info(f"Transcription successful: {result['text']}")
        return result['text']
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")


def process_video(url: str, user_id: int, task_id: int):
    db = next(get_db())
    try:
        audio_filename = extract_audio(url)
        transcribed_text = transcribe_audio(audio_filename)
        db_video = db.query(Video).filter(Video.id == task_id).first()
        if not db_video:
            logger.error(f"Video with task_id {task_id} not found")
            return
        db_video.transcribed = transcribed_text
        db.commit()
        logger.info(f"Database commit successful for video ID: {db_video.id}")
        db.refresh(db_video)
        logger.info(f"Video processed and saved: {db_video.id}")
        logger.info(f"Transcription: {transcribed_text}")
        return db_video.id
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")
    finally:
        db.close()