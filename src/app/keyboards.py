
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.replies import choose_channel_button, choose_file_button, choose_video_button

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=choose_video_button)],
    [KeyboardButton(text=choose_channel_button)],
    [KeyboardButton(text=choose_file_button)],
], resize_keyboard=True, input_field_placeholder="Выберете действие...")

options_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎥 скачать видео", callback_data="download_video")],
    [InlineKeyboardButton(text="🎧 скачать аудио", callback_data="download_audio")],
    [InlineKeyboardButton(text="💬 скачать субтитры", callback_data="download_text")],
])

get_phone = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="отправить номер", request_contact=True)],
], resize_keyboard=True)
