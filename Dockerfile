FROM python:3.12

WORKDIR /app

COPY . /app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -e . -U

CMD ["python3", "src/bot.py"]