DOCKER_PREFIX=punkadiddle
DOCKER_NAME=concourse-pypi-resource
.PHONY: all clean clean_test dist testenv

all: dist

clean: clean_test
	rm -rf .eggs/ .pytest_cache/ .venv/ *.egg-info/ dist/
	docker rmi -f $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '$(DOCKER_NAME)') 2>/dev/null || true

clean_test:
	find test/ -maxdepth 2 -type d -name 'build' -or -name 'dist' -or -name '*.egg-info' | xargs -I'{}' rm -rf '{}'
	rm -rf test/test_dist/

Pipfile.lock: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv --three lock

.venv/.installed: Pipfile.lock
	PIPENV_VENV_IN_PROJECT=1 pipenv --three install --dev
	touch .venv/.installed

test/test_dist: clean_test
	find test/ -maxdepth 1 -type d -name 'test_package*' | xargs -I'{}' /bin/sh -c "cd '{}'; python3 setup.py bdist_egg; python3 setup.py bdist_wheel; python3 setup.py sdist"
	find test/ -maxdepth 1 -type d -name 'test_package*' | xargs -I'{}' /bin/sh -c "cd '{}'; python2 setup.py bdist_wheel; python2 setup.py sdist"
	mkdir test/test_dist
	find test -type f -path 'test/test_package*/dist/*' | xargs -I'{}' mv -v '{}' test/test_dist/
	rm test/test_dist/test_package1-1.0.1rc1-py2*

test: test/test_dist .venv/.installed
	pipenv run pytest test/unittests.py

dist: .venv/.installed 
	rm -f dist/*
	pipenv run python setup.py sdist

	docker rmi -f $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '$(DOCKER_NAME)') 2>/dev/null || true

	version=$$(cat .version) && \
	docker build . \
		--tag "$(DOCKER_NAME):latest" \
		--tag "$(DOCKER_NAME):$$version" \
		--tag "$(DOCKER_PREFIX)/$(DOCKER_NAME):latest-rc" \
		--tag "$(DOCKER_PREFIX)/$(DOCKER_NAME):$$version" && \
	echo "$$version" > dist/.docker-version

	pipenv run python -c "import semver; v=open('.version', 'r').read(); v=semver.bump_prerelease(v); open('.version', 'w').write(v)"
	echo -e "#\nnext version is $$(cat .version)\n#\n#"
	docker images | grep '$(DOCKER_NAME)'

push: 
	version=$$(cat dist/.docker-version) && \
	docker push "$(DOCKER_PREFIX)/$(DOCKER_NAME):$$version" && \
	docker push "$(DOCKER_PREFIX)/$(DOCKER_NAME):latest-rc"