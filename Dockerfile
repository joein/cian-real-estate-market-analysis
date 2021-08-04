FROM python:3.8.11-slim-buster as base

FROM base as builder
COPY requirements.txt ./

RUN apt update && \
pip3 install virtualenv==20.0.33 && \
virtualenv -p /usr/local/bin/python3.8 /venv --always-copy && \
/venv/bin/pip3 install -r requirements.txt

COPY ./src /usr/src/app

FROM base

COPY --from=builder /venv /venv
COPY --from=builder /usr/src/app /usr/src/app

WORKDIR /usr/src/app

CMD ["/bin/bash", "-i"]
