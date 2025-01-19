FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libssl-dev \
    build-essential \
    default-jdk \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome-stable_current_amd64.deb \
    && wget -q https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.83/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip -d /usr/bin/ \
    && rm chromedriver-linux64.zip \
    && apt-get clean

ENV PATH="/usr/bin/chromedriver-linux64:${PATH}"

COPY . /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["sh", "-c", "gunicorn -w 2 --timeout 120 -b 0.0.0.0:$PORT app:app"]