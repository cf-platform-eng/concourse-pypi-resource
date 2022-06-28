# must match the Python version configured in Pipfile
FROM python:3.9

COPY dist/concourse_pypi_resource-*.whl .
RUN pip install concourse_pypi_resource-*.whl && \
    mkdir -p /opt/resource && \
    for script in check in out; do ln -sv $(which $script) /opt/resource/; done

RUN rm concourse_pypi_resource-*.whl
