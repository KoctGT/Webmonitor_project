FROM python:3
LABEL name="webmonitor_backend"
ENV PYTHONUNBUFFERED 1
RUN mkdir /webmonitor_backend
RUN mkdir /ssh_key
WORKDIR /webmonitor_backend
COPY requirements.txt /webmonitor_backend/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN apt-get update && apt-get install -y iputils-ping
ADD ./project/ /webmonitor_backend/
ADD ./ssh_key/ /ssh_key/
