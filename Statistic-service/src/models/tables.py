from sqlalchemy import JSON, Column, Float, Integer, String
from src.database import Base


class Statistic(Base):
    __tablename__ = "statistic"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    task_id = Column(String, nullable=False)
    description = Column(String, nullable=True)
    output = Column(JSON, nullable=False)
    time = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    advice = Column(String, nullable=False)