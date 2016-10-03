FROM python:3-alpine
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir -p /opt/resource
COPY bin/* /opt/resource/
