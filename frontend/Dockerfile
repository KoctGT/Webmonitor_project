FROM python:3
LABEL name="webmonitor_frontend"
ENV PYTHONUNBUFFERED 1
RUN mkdir /webmonitor_frontend
WORKDIR /webmonitor_frontend
COPY requirements.txt /webmonitor_frontend/
RUN pip install --upgrade pip && pip install -r requirements.txt
# ADD ./project/ /webmonitor_frontend/
