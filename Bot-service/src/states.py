from aiogram.fsm.state import State, StatesGroup

class RouteStates(StatesGroup):
    """Состояния для создания маршрута"""
    waiting_interests = State()      
    waiting_time = State()           
    waiting_location = State()       
    processing = State()             


class AuthStates(StatesGroup):
    """Состояния для авторизации"""
    waiting_email = State()         
    waiting_password = State()       