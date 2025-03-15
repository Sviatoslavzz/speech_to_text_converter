welcome_message = {"ru":
                       "Добро пожаловать в бота по скачиванию и транскрибации YouTube видео 👋\n"
                       "Что я умею? 🤔\n"
                       "🔹 Скачаю видео по YouTube ссылке\n"
                       "🔹 Скачаю аудио по YouTube ссылке\n"
                       "🔹 Скачаю субтитры, а если их нет у видео - "
                       "запущу транскрибацию и все равно пришлю субтитры 🥰\n"
                       "🔹 Могу сделать все вышеперечисленное сразу для всех видео с YouTube канала - "
                       "для этого нужна ссылка на канал.\n"
                       "🔹 И на десерт - могу сделать транскрипцию по твоему аудио/видео файлу 🥹\n\n"
                       "Enjoy 😎",
                   "en":
                       "Welcome to Talkushka chat-bot 👋\n"
                       "What am I capable of? 🤔\n"
                       "🔹 I can download a video by YouTube link\n"
                       "🔹 I can download a audio by YouTube link\n"
                       "🔹 I can download a subtitles by YouTube link, and in case of missing - "
                       "may run transcriber and still send subtitles 🥰\n"
                       "🔹 I can perform all the above for a whole YouTube channel.\n"
                       "🔹 And for dessert - I can make a transcription from your audio/video file 🥹\n\n"
                       "Enjoy 😎"
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

external_storage_ms = {
    "ru": "💥 Видео: {title}\nПрикрепляю ссылку на внешнее хранилище:\n{link}\n{message}",
    "en": "💥 Video: {title}\nLink to external storage below:\n{link}\n{message}"
}
