
.PHONY: uninstall_all_dependencies

run:
	python3 src/main.py

install:
	pip install -r requirements.txt -U

uninstall_all_dependencies:
	pip freeze | grep -v '^-e' | xargs pip uninstall -y
	pip cache purge