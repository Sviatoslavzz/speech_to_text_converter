from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from talkushka_service.app.replies import choose_channel_button, choose_file_button, choose_video_button
from talkushka_service.objects import VideoOptions

main_menu = {
    "ru": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=choose_video_button["ru"]), ],
            [KeyboardButton(text=choose_channel_button["ru"])],
            [KeyboardButton(text=choose_file_button["ru"])],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    ),
    "en": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=choose_video_button["en"])],
            [KeyboardButton(text=choose_channel_button["en"])],
            [KeyboardButton(text=choose_file_button["en"])],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action...",
    )
}

help_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="сменить язык", callback_data="change_language")],
            [InlineKeyboardButton(text="обратиться в поддержку", callback_data="contact_helpdesk")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="change language", callback_data="change_language")],
            [InlineKeyboardButton(text="contact helpdesk", callback_data="contact_helpdesk")],
        ]
    ),
}

approve_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="подтвердить", callback_data="approve")],
            [InlineKeyboardButton(text="отменить", callback_data="cancel")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="approve", callback_data="approve")],
            [InlineKeyboardButton(text="cancel", callback_data="cancel")],
        ]
    ),
}

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
