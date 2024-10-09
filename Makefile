include .env
export

.PHONY: uninstall_all_dependencies

run_bot:
	python3 src/bot.py

run_cli:
	python3 src/main.py

install:
	pip install -e .[dev,test] -U

uninstall_all_dependencies:
	pip freeze | grep -v '^-e' | xargs pip uninstall -y
	pip cache purge

test:
	pytest tests/

lint:
	ruff check .
	ruff format . --check

format:
	ruff check . --fix
	ruff format .

clean:
	@echo "🧹🧹🧹 perfect"
	@rm -rf *.egg_info __pycache__ build/