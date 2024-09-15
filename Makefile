include .env
export

.PHONY: uninstall_all_dependencies

run:
	python3 src/main.py

install:
	pip install -e .[dev,test] -U

uninstall_all_dependencies:
	pip freeze | grep -v '^-e' | xargs pip uninstall -y
	pip cache purge

lint:
	ruff check .
	ruff format . --check

format:
	ruff check . --fix
	ruff format .

clean:
	rm -rf *.egg_info