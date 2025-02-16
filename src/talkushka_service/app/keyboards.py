from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from talkushka_service.app.replies import choose_channel_button, choose_file_button, choose_video_button
from talkushka_service.objects import VideoOptions

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=choose_video_button)],
        [KeyboardButton(text=choose_channel_button)],
        [KeyboardButton(text=choose_file_button)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие...",
)

action_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎥 скачать видео", callback_data="download_video")],
        [InlineKeyboardButton(text="🎧 скачать аудио", callback_data="download_audio")],
        [InlineKeyboardButton(text="💬 скачать субтитры", callback_data="download_text")],
    ]
)

option_chooser_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🥷🏼 Выбирать качество отдельно для каждого видео", callback_data="single_option")],
        [InlineKeyboardButton(text="🗿 Выбрать качество для всех сразу", callback_data="multi_option")],
    ]
)

standard_video_options_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="144p - 30 fps", callback_data="256:144:30")],
        [InlineKeyboardButton(text="240p - 30 fps", callback_data="426:240:30")],
        [InlineKeyboardButton(text="360p - 30 fps", callback_data="640:360:30")],
        [InlineKeyboardButton(text="480p - 30 fps", callback_data="854:480:30")],
        [
            InlineKeyboardButton(text="720p - 30 fps", callback_data="1280:720:30"),
            InlineKeyboardButton(text="720p - 60 fps", callback_data="1280:720:60"),
        ],
        [
            InlineKeyboardButton(text="1080p - 30 fps", callback_data="1920:1080:30"),
            InlineKeyboardButton(text="1080p - 60 fps", callback_data="1920:1080:60"),
        ],
        [
            InlineKeyboardButton(text="1440p - 30 fps", callback_data="2560:1440:30"),
            InlineKeyboardButton(text="1440p - 60 fps", callback_data="2560:1440:60"),
        ],
        [
            InlineKeyboardButton(text="2160p - 30 fps", callback_data="3840:2160:30"),
            InlineKeyboardButton(text="2160p - 60 fps", callback_data="3840:2160:60"),
        ],
    ]
)

proceed_simple_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🥷🏼 Да", callback_data="single_option")],
        [InlineKeyboardButton(text="🗿 Нет", callback_data="cancel")],
    ]
)


def generate_option_keyboard(options: list[VideoOptions]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{option.width}x{option.height} : fps {option.fps}", callback_data=option.__str__()
                )
            ]
            for option in options
        ]
    )
