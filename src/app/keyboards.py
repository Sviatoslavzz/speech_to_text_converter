from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.replies import choose_channel_button, choose_file_button, choose_video_button
from objects import VideoOptions

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=choose_video_button)],
        [KeyboardButton(text=choose_channel_button)],
        [KeyboardButton(text=choose_file_button)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие...",
)

options_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎥 скачать видео", callback_data="download_video")],
        [InlineKeyboardButton(text="🎧 скачать аудио", callback_data="download_audio")],
        [InlineKeyboardButton(text="💬 скачать субтитры", callback_data="download_text")],
    ]
)

video_options_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🥷🏼 Выбирать качество отдельно для каждого видео", callback_data="single_option")],
        [InlineKeyboardButton(text="🗿 Выбрать качество для всех сразу", callback_data="multi_option")],
    ]
)

proceed_simple_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🥷🏼 Да", callback_data="single_option")],
        [InlineKeyboardButton(text="🗿 Нет", callback_data="cancel")],
    ]
)

# get_phone = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text="отправить номер", request_contact=True)],
#     ],
#     resize_keyboard=True,
# )


def generate_option_keyboard(options: list[VideoOptions]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"{option.width}x{option.height} : fps {option.fps}",
                                               callback_data=option.__str__())] for option in options]
    )
