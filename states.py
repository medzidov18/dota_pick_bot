from aiogram.fsm.state import State, StatesGroup

class PickStates(StatesGroup):
    waiting_position = State()
    waiting_enemies = State()