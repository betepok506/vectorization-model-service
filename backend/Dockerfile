FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100

ENV HTTP_PROXY="http://130.100.7.222:1082"
ENV HTTPS_PROXY="http://130.100.7.222:1082"

RUN echo 'Acquire::http::Proxy "http://130.100.7.222:1082";' > /etc/apt/apt.conf.d/00aptproxy

# Install Poetry
RUN apt clean && apt update && apt install curl -y
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/Makefile /code/

WORKDIR /code
# RUN make install
# Allow installing dev dependencies to run tests
# ARG INSTALL_DEV=false
# RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"
RUN poetry config virtualenvs.create false
RUN pip install --upgrade pip


RUN make install
ENV PYTHONPATH=/code

CMD ["tail", "-f", "/dev/null"]
