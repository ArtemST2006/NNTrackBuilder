from aiogram.fsm.state import State, StatesGroup

class RouteStates(StatesGroup):
    waiting_interests = State()      
    waiting_time = State()           
    waiting_location = State()      
    processing = State()            