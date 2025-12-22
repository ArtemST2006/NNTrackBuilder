import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


# спросить у дениса
class PlaceItem(BaseModel):
    coordinates: str
    description: str


class AIResponse(BaseModel):
    user_id: int
    task_id: str
    output: List[PlaceItem]
    description: str
    time: float
    long: float
    advice: str

    model_config = ConfigDict(from_attributes=True)


class StatisticResponse(BaseModel):
    statistic: List[AIResponse]
