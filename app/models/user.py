# app/models/user.py
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(BigInteger, nullable=False)
    password = Column(String(255), nullable=False)
    videos = relationship("Video", back_populates="user")
    chathistories = relationship("ChatHistory", back_populates="user")
    
    
class UserCreate(BaseModel):
    name: str
    phone: int
    password:str




class login(BaseModel):
    name:str
    password:str