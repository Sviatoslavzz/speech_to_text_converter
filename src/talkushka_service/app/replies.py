from talkushka_service.db.model import SubscriptionType
from talkushka_service.model.objects import AppOperation

welcome_message = {"ru":
                       "Привет! Я Толкушка 👋\n"
                       "Что я умею? 🤔\n\n"
                       "1️⃣Действия с YouTube видео:\n"
                       "🔹 Скачаю видео в нужном качестве\n"
                       "🔹 Скачаю аудио\n"
                       "🔹 Скачаю субтитры к видео\n"
                       "🔹 Могу сделать все вышеперечисленное сразу для всех видео с канала - "
                       "для этого нужна ссылка на канал.\n\n"
                       "2️⃣Генерация текста:\n"
                       "🔹 Могу сгенерировать текст по твоему аудио или видео файлу 🥹\n\n"
                       "Наслаждайся 😎",
                   "en":
                       "Welcome to Talkushka chat-bot 👋\n"
                       "What am I capable of? 🤔\n\n"
                       "🔹 I can download a video by YouTube link with required quality\n"
                       "🔹 I can download an audio by YouTube link\n"
                       "🔹 I can download subtitles by YouTube link\n"
                       "🔹 I can perform all the above for all YouTube channel videos.\n"
                       "🔹 I can make a transcription for your audio or video file 🥹\n\n"
                       "Enjoy 😎"
                   }

limits_info_message = {"ru": "Сейчас я нахожусь в режиме бета тестирования.\n"
                             "Каждый день ты бесплатно можешь скачать {video_limit} видео, {audio_limit} аудио, "
                             "{subtitle_limit} субтитров и сделать {transcription_limit} транскрипций.\n"
                             "Лимиты обновляются в {reset_hour}:00 по Мск.",
                       "en": "Now is beta testing time.\n"
                             "Every day you can download {video_limit} videos, {audio_limit} audios, "
                             "{subtitle_limit} subtitles and request {transcription_limit} transcriptions.\n"
                             "Limits are reset on {reset_hour}:00 Moscow tz."
                       }

provide_links = {
    "ru": "Вставь ссылку / ссылки в следующем сообщении (не забудь разделить их пробелом или переносом строки)",
    "en": "Paste a link / links in the next message (do not forget to separate them by space or new line)",
}

provide_channel = {
    "ru": "Вставь ссылку на YouTube канал в следующем сообщении",
    "en": "Paste a link to YouTube channel in the next message",
}

provide_file = {
    "ru": "Прикрепи файл следующим сообщением",
    "en": "Attach a file as a next message",
}

choose_video_button = {"ru": "🎥 хочу поработать с отдельными видео",
                       "en": "🎥 handle a single video link"}

choose_channel_button = {"ru": "🦄 хочу поработать с каналом",
                         "en": "🦄 handle a channel link"}

choose_file_button = {"ru": "🗂️ хочу загрузить файл и получить транскрипцию",
                      "en": "🗂️ upload my file to get the transcription"}

help_reply = {"ru": "Чтобы посмотреть инструкцию бота используй команду /start.\nИли выбери действие",
              "en": "To check bot instruction use the /start command.\nOr choose an action"}

change_language_reply = {"ru": "У тебя установлен язык '{lc}'",
                         "en": "You current language setting if '{lc}'"}

language_changed = {"ru": "Вы успешно сменили язык бота на русский",
                    "en": "Bot language has been successfully changed to English"}

contact_helpdesk_reply = {"ru": "Напиши свое обращение следующим сообщением",
                          "en": "Describe your request in a single message"}

validate_helpdesk_message_reply = \
    {"ru": "Твое обращение:\n\n{r}\n\nМы также передадим id твоего чата и твой nickname.",
     "en": "Your request:\n\n{r}\n\nYour nickname and chat_id will be passed to helpdesk."}

helpdesk_sent_reply = {"ru": "Спасибо! Твое обращение успешно отправлено в поддержку.",
                       "en": "Thanks! Your request has been successfully sent to helpdesk."}

cancel_reply = {"ru": "Галя, у нас отмена!",
                "en": "Cancelled"}

helpdesk_mess = "🚨 Helpdesk request:\nusername:{un}\nuser_id {uid}\n\n"

channel_not_found = {
    "ru": "❌ Не нашел канал по данной ссылке {ch_link}",
    "en": "❌ Channel is not found by provided link {ch_link}",
}

video_not_found_in_channel = {
    "ru": "❌ Не нашел видео на данном канале",
    "en": "❌ Videos are not found on the channel",
}

channel_videos_found = {
    "ru": "✅ Нашел {amount} видео на канале {channel_name}",
    "en": "✅ Found {amount} videos on channel {channel_name}",
}

video_found = {
    "ru": "✅ Нашел видео {title}",
    "en": "✅ Found video {title}",
}

choose_action = {
    "ru": "Тогда выбирай действие 🏄‍♂️",
    "en": "Choose an option 🏄‍♂️",
}

video_links_not_found = {
    "ru": "Не нашел корректные ссылки.",
    "en": "Correct links not found",
}

wrong_file_format = {
    "ru": "Упс, кажется такой файл не подойдет ☹️",
    "en": "Ops, I cannot accept this file type ☹️",
}

in_progress = {
    "ru": "Принято в работу!",
    "en": "Work in progress!",
}

transcriber_unavailable = {
    "ru": "К сожалению, сервис транскрибации недоступен в данный момент 😓",
    "en": "Unfortunately, transcriber service is unavailable now 😓",
}

option_search = {
    "ru": "Ищу доступные опции для видео..",
    "en": "Searching for available video options..",
}

available_options = {
    "ru": "Доступные опции для видео {title}",
    "en": "Available options for the video {title}",
}

how_to_choose_option = {
    "ru": "Как предпочитаешь выбирать качество видео?",
    "en": "How would you like to choose video quality?",
}

option_search_expl = {
    "ru": "Поиск осуществляется <= выбранной опции",
    "en": "Search is made <= chosen option",
}

continue_msg = {
    "ru": "Продолжаем?",
    "en": "Approve to proceed",
}

videos_downloaded = {
    "ru": "Мы скачали все видео",
    "en": "All videos downloaded",
}

file_limit = {
    "ru": "К сожалению, лимит бесплатных транскрибаций на сегодня исчерпан.",
    "en": "Unfortunately, the limit of free transcribings is expired for today.",
}

video_limit = {
    "ru": "К сожалению, лимит бесплатных загрузок видео на сегодня исчерпан.",
    "en": "Unfortunately, the limit of free video downloads is expired for today.",
}

audio_limit = {
    "ru": "К сожалению, лимит бесплатных загрузок аудио на сегодня исчерпан.",
    "en": "Unfortunately, the limit of free audio downloads is expired for today.",
}

subtitle_limit = {
    "ru": "К сожалению, лимит бесплатных загрузок субтитров на сегодня исчерпан.",
    "en": "Unfortunately, the limit of free subtitle downloads is expired for today.",
}


def get_limit_reply(parameter: AppOperation, language_code: str) -> str:
    if parameter == AppOperation.TRANSCRIPTION:
        return file_limit[language_code]
    if parameter == AppOperation.AUDIO:
        return audio_limit[language_code]
    if parameter == AppOperation.VIDEO:
        return video_limit[language_code]
    return subtitle_limit[language_code]


external_storage_ms = {
    "ru": "💥 Видео: {title}\nПрикрепляю ссылку на внешнее хранилище:\n{link}\n{message}",
    "en": "💥 Video: {title}\nLink to external storage below:\n{link}\n{message}"
}

create_promocode_msg = {
    "ru": "Выбери как ты хочешь создать промокод",
    "en": "Choose how you want to create promocode"
}

custom_promocode = {
    "ru": "Введи промокод в следующем сообщении",
    "en": "Write a custom promocode in the next message",
}

promocode_create_success = {
    "ru": "Промокод успешно создан: {code}",
    "en": "Promocode is created successfully: {code}",
}

promocode_create_fail = {
    "ru": "Произошла ошибка, попробуй сначала",
    "en": "Some error occurred, start over",
}

choose_promocode_subscription_type = {
    "ru": "Выбери тип подписки по промокоду",
    "en": "Choose a promocode subscription type",
}

choose_promocode_total_use = {
    "ru": "Сколько раз можно будет использовать промокод? Введи число",
    "en": "Write a total promocode use in the next message as a number",
}

promocode = {
    "ru": "У тебя есть промокод? Отлично! Введи его следующим сообщением",
    "en": "You have a promo code? Great! Please send it in the next message"
}

promocode_success = {
    "ru": "Вы успешно применили промокод.\nАктивирована подписка: {subscription}",
    "en": "Promo code is applied successfully.\nSubscription activated: {subscription}"
}

promocode_not_found = {
    "ru": "Промокод не найден",
    "en": "Promo code is not found"
}

promocode_worse_subscription = {
    "ru": "Попробуйте применить другой промокод либо дождитесь окончания действия подписки",
    "en": "Try to use another promocode or wait till the current subscription is expired"
}

subscription_expired = {
    "ru": "Ваша подписка истекла.\nЧтобы оформить новую подписку воспользуйся командой\n/GET_SUBSCRIPTION",
    "en": "Your current subscription is expired.\nTo get a new one please use the command\n/GET_SUBSCRIPTION"
}


def get_subscription_message(subscription_type: SubscriptionType, language_code: str) -> str:
    week_msg = {
        "ru": "одна неделя безлимитной загрузки",
        "en": "a week of unlimited downloads",
    }
    month_msg = {
        "ru": "один месяц безлимитной загрузки",
        "en": "a month of unlimited downloads",
    }
    year_msg = {
        "ru": "один год безлимитной загрузки",
        "en": "a year of unlimited downloads",
    }
    lifetime_msg = {
        "ru": "вечная безлимитная загрузка",
        "en": "eternal unlimited downloads",
    }
    if subscription_type == SubscriptionType.week:
        return week_msg[language_code]
    if subscription_type == SubscriptionType.month:
        return month_msg[language_code]
    if subscription_type == SubscriptionType.year:
        return year_msg[language_code]
    return lifetime_msg[language_code]
