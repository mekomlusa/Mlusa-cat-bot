FROM python:3.6-slim-buster
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean

COPY requirements-docker.txt /tmp/

RUN pip install -r /tmp/requirements-docker.txt

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

COPY dailyCatie.py .
COPY dbhelper.py .

CMD python ./dailyCatie.py