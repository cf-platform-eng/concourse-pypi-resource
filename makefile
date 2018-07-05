DOCKER_PREFIX=
DOCKER_NAME=concourse_py_resource

.PHONY: all clean dist

all: dist

clean:
	rm -rf .eggs/ .pytest_cache/ .venv/ *.egg-info/ dist/
	docker rmi -f $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '$(DOCKER_NAME)') 2>/dev/null || true

Pipfile.lock: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv --three lock

.venv/.installed: Pipfile.lock
	PIPENV_VENV_IN_PROJECT=1 pipenv --three install --dev
	touch .venv/.installed

test: .venv/.installed
	pipenv run pytest test/unittests.py

dist:
	rm -f dist/*
	pipenv run python setup.py sdist

	docker rmi -f $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '$(DOCKER_NAME)') 2>/dev/null || true

	version=$$(pipenv run python setup.py --version) && \
	docker build . \
		--tag "$(DOCKER_NAME):latest" \
		--tag "$(DOCKER_NAME):$$version" \
		--tag "$(DOCKER_PREFIX)$(DOCKER_NAME):latest"
