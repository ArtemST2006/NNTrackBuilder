from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func
from src.database import Base

class Statistic(Base):
    __tablename__ = "statistic"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    task_id = Column(String, nullable=False)
    description = Column(String, nullable=True)
    output = Column(JSON, nullable=False)
    time = Column(DateTime, default=func.now())
    long = Column(Float, nullable=False)
    advice = Column(String, nullable=False)