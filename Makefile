include .env
export

WHISPER_PROTO_DIR = src/proto_gen/whisper

.PHONY: uninstall_all_dependencies

run_bot:
	@echo "Launching telegram bot app"
	run_bot

run_cli:
	@echo "Launching cli mode"
	run_cli

install:
	pip install -e . -U

install_dev:
	pip install -e .[dev,test] -U

uninstall_all_dependencies:
	pip freeze | grep -v '^-e' | xargs pip uninstall -y
	pip cache purge

gen_whisper_proto: $(WHISPER_PROTO_DIR)
	python -m grpc_tools.protoc -I . --python_betterproto_out=$(WHISPER_PROTO_DIR) proto/whisper/talkushka_whisper.proto

test:
	pytest tests/

lint:
	ruff check .
	ruff format . --check

format:
	ruff check . --fix
	ruff format .

clean:
	rm -rf src/*.egg-info *.egg_info __pycache__ build/
	@echo "🧹🧹🧹 perfect"

$(WHISPER_PROTO_DIR):
	mkdir -p $(WHISPER_PROTO_DIR)