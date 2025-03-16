FROM python:3.12

WORKDIR /talkushka-service

COPY . /talkushka-service

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install --no-cache-dir . -U

ENTRYPOINT ["talkushka_service"]