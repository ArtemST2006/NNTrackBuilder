from aiogram.fsm.state import State, StatesGroup

class RouteStates(StatesGroup):
    """Состояния для создания маршрута"""
    waiting_interests = State()      # Ждем выбор интересов
    waiting_time = State()           # Ждем ввод времени
    waiting_location = State()       # Ждем локацию/адрес
    processing = State()             # Обрабатываем запрос


class AuthStates(StatesGroup):
    """Состояния для авторизации"""
    waiting_email = State()          # Ждем email
    waiting_password = State()       # Ждем пароль