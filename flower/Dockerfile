# pull official base image
FROM python:3.10-slim

ENV HTTP_PROXY="http://130.100.7.222:1082"
ENV HTTPS_PROXY="http://130.100.7.222:1082"

RUN echo 'Acquire::http::Proxy "http://130.100.7.222:1082";' > /etc/apt/apt.conf.d/00aptproxy

WORKDIR /app
COPY . .
# RUN pip install --upgrade pip
RUN pip install poetry

# RUN apt clean && apt update && apt install curl -y
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    # cd /usr/local/bin && \
    # ln -s /opt/poetry/bin/poetry
RUN poetry config virtualenvs.create false
RUN poetry install 


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# RUN poetry install

# copy project