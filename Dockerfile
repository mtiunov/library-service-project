FROM python:3.10.14-alpine3.20
LABEL maintainer="tiunovmixs@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN adduser \
    --disabled-password \
    --no-create-home \
    my_user

USER my_user
