from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from talkushka_service.app.replies import choose_channel_button, choose_file_button, choose_video_button
from talkushka_service.model.objects import VideoOptions

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

action_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎥 скачать видео", callback_data="download_video")],
            [InlineKeyboardButton(text="🎧 скачать аудио", callback_data="download_audio")],
            [InlineKeyboardButton(text="💬 скачать субтитры", callback_data="download_text")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎥 download video", callback_data="download_video")],
            [InlineKeyboardButton(text="🎧 download audio", callback_data="download_audio")],
            [InlineKeyboardButton(text="💬 download subtitles", callback_data="download_text")],
        ]
    )
}

option_chooser_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥷🏼 Выбирать качество отдельно для каждого видео",
                                  callback_data="single_option")],
            [InlineKeyboardButton(text="🗿 Выбрать качество для всех сразу", callback_data="multi_option")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥷🏼 Choose quality for a single video",
                                  callback_data="single_option")],
            [InlineKeyboardButton(text="🗿 Choose quality for all videos once", callback_data="multi_option")],
        ]
    )
}

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

proceed_simple_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥷🏼 Да", callback_data="single_option")],
            [InlineKeyboardButton(text="🗿 Нет", callback_data="cancel")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥷🏼 Yes", callback_data="single_option")],
            [InlineKeyboardButton(text="🗿 No", callback_data="cancel")],
        ]
    )
}


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

change_language_menu = {
    "ru": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="сменить на русский", callback_data="lc_to_ru")],
            [InlineKeyboardButton(text="сменить на английский", callback_data="lc_to_en")],
        ]
    ),
    "en": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="change to russian", callback_data="lc_to_ru")],
            [InlineKeyboardButton(text="change to english", callback_data="lc_to_en")],
        ]
    ),
}
