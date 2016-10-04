FROM python:3-alpine
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir -p /opt/resource
COPY pypi_resource/check.py /opt/resource/check
COPY pypi_resource/in_.py /opt/resource/in
COPY pypi_resource/out.py /opt/resource/out
RUN chmod +x /opt/resource/check /opt/resource/in /opt/resource/out
