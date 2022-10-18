# syntax=docker/dockerfile:1
FROM python:3.10-alpine3.16
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./app/client.py .