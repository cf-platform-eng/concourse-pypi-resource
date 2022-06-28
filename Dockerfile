# must match the Python version configured in Pipfile
FROM python:3.9

COPY dist/concourse-pypi-resource-*.tar.gz .
RUN pip install concourse-pypi-resource-*.tar.gz && \
    mkdir -p /opt/resource && \
    for script in check in out; do ln -sv $(which $script) /opt/resource/; done
