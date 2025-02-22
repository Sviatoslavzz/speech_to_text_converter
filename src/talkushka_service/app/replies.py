welcome_message = """
Добро пожаловать в бота по скачиванию и транскрибации YouTube видео 👋
Что я умею? 🤔
🔹 Скачаю видео по YouTube ссылке
🔹 Скачаю аудио по YouTube ссылке
🔹 Скачаю субтитры, а если их нет у видео - запущу транскрибацию и все равно пришлю субтитры 🥰
🔹 Могу сделать все вышеперечисленное сразу для всех видео с YouTube канала - для этого нужна ссылка на канал.
🔹 И на десерт - могу сделать транскрипцию по твоему аудио/видео файлу 🥹

Enjoy 😎
"""

provide_links = "Вставь ссылку / ссылки в следующем сообщении (не забудь разделить их пробелом или переносом строки)"

provide_channel = "Вставь ссылку на YouTube канал в следующем сообщении"

provide_file = "Прикрепи файл следующим сообщением"

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
