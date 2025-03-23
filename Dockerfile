FROM sviatoslavzz/telegram-server-py312:8.3

WORKDIR /talkushka-service

COPY . /talkushka-service

RUN apt-get install -y ffmpeg

RUN pip install --upgrade pip && pip install --no-cache-dir . -U
