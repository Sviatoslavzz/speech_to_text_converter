from aiogram.fsm.state import State, StatesGroup


class UserRoute(StatesGroup):
    option = State()  # str : video | channel | file
    videos = State()  # [links] | channel link
    file = State()
    action = State()  # str : download_video | download_audio | download_text
    load_options = State()  # [VideoOptions] | str(width:height:fps)
    single_video_options = State()
    multi_video_options = State()


class HelpRoute(StatesGroup):
    validation = State()
    approve = State()

class PromocodeRoute(StatesGroup):
    receive = State()
