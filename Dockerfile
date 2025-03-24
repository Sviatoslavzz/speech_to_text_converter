FROM sviatoslavzz/telegram-server-py312:latest

WORKDIR /talkushka-service

COPY cert/ /talkushka-service/cert
COPY src/ /talkushka-service/src
COPY pyproject.toml /talkushka-service

RUN pip install --upgrade pip && pip install --no-cache-dir . -U
