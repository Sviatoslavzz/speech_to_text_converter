UV_ENV_FILE ?= .env
PROJECT_BINARY := talkushka-service
WHISPER_PROTO_DIR := src/proto_gen/whisper

ifneq ($(wildcard $(ENV_FILE_PATH)),)
UV_ENV_FILE ?= $(ENV_FILE_PATH)
export UV_ENV_FILE
endif

.DEFAULT_GOAL := help

.PHONY: help run install install-dev upgrade lock uninstall test lint-format lint-check \
	healthcheck clean gen_whisper_proto gen_client_cert docker_build_and_push \
	_sync-all _tools-install _hooks-install git-sync-with-remote

help:
	@printf '%s\n' \
		'Usage: make <target>' \
		'' \
		'UV is required.' \
		'  macOS: brew install uv' \
		'  Linux: curl -LsSf https://astral.sh/uv/install.sh | sh' \
		'  Verify: uv --version' \
		'' \
		'Public targets:' \
		'  help                   Show this help and UV installation tips' \
		'  run                    Run the $(PROJECT_BINARY) with production dependencies' \
		'  install                Install production dependencies into .venv' \
		'  install-dev            Install all dependencies and configure development hooks' \
		'  upgrade                Upgrade all locked dependencies' \
		'  lock                   Create or update uv.lock' \
		'  uninstall              Remove the project environment and UV cache' \
		'  test                   Run pytest' \
		'  lint-format            Format the project and apply Ruff fixes' \
		'  lint-check             Check Ruff lint and formatting without changing files' \
		'  healthcheck            Run formatting and lockfile checks' \
		'  clean                  Remove build artifacts' \
		'  gen_whisper_proto      Generate whisper gRPC stubs' \
		'  gen_client_cert        Generate client TLS certificate' \
		'  docker_build_and_push  Build and push amd64 image' \
		'  git-sync-with-remote   Sync develop with origin and prune stale local branches'

run:
	uv run --locked --no-dev $(PROJECT_BINARY)

install:
	uv sync --locked --no-default-groups

install-dev: _sync-all _hooks-install _tools-install

upgrade:
	uv sync --upgrade --all-groups

lock:
	uv lock

test:
	uv run --locked --group test pytest tests/

uninstall:
	uv venv --clear .venv
	uv cache clean

lint-format:
	uvx ruff check . --fix
	uvx ruff format .

lint-check:
	uvx ruff check .
	uvx ruff format . --check

healthcheck: lint-format
	uv lock --check

clean:
	rm -rf src/*.egg-info *.egg_info __pycache__ build/
	@echo "🧹🧹🧹 perfect"

gen_whisper_proto: $(WHISPER_PROTO_DIR)
	uv run --locked --group dev python -m grpc_tools.protoc \
		-I . --python_betterproto_out=$(WHISPER_PROTO_DIR) \
		proto/whisper/talkushka_whisper.proto

gen_client_cert:
	openssl genrsa -out cert/client.key 4096
	openssl req -new -key cert/client.key -out cert/client.csr \
		-subj "/C=RU/ST=State/L=City/O=Organization/OU=ClientUnit/CN=talkushka"
	openssl x509 -req -in cert/client.csr -CA cert/ca.crt -CAkey cert/ca.key \
		-CAcreateserial -out cert/client.crt -days 365 -sha256

docker_build_and_push:
	docker buildx build --platform linux/amd64 \
		--tag sviatoslavzz/talkushka-service:latest \
		--push .

# Sync local git with remote: switch to develop, fetch --prune, delete stale local branches.
# Never deletes: master, main, dev, develop.
git-sync-with-remote:
	@set -e; \
	echo "WARNING: This will force-delete (-D) all local branches that have no matching origin/<name>."; \
	echo "         Protected (never deleted): master, main, dev, develop."; \
	printf "Continue? [y/N] "; \
	read ans </dev/tty; \
	case "$$ans" in \
		y|Y) ;; \
		*) echo "Aborted."; exit 1 ;; \
	esac; \
	current=$$(git branch --show-current); \
	if [ "$$current" != "develop" ]; then \
		if [ -n "$$(git status --porcelain)" ]; then \
			echo "Uncommitted changes on '$$current' — commit/stash first, then re-run."; \
			exit 1; \
		fi; \
		echo "Switching $$current → develop"; \
		git switch develop; \
	fi; \
	echo "Fetching remote (prune stale remote-tracking refs)..."; \
	git fetch --prune origin; \
	echo "Fast-forwarding develop..."; \
	git pull --ff-only origin develop; \
	echo "Pruning stale local branches..."; \
	for branch in $$(git for-each-ref --format='%(refname:short)' refs/heads/); do \
		case "$$branch" in \
			master|main|dev|develop) continue ;; \
		esac; \
		if ! git show-ref --verify --quiet "refs/remotes/origin/$$branch"; then \
			echo "  -D $$branch (no origin/$$branch)"; \
			git branch -D "$$branch"; \
		fi; \
	done; \
	echo "Done."


#=============================== PRIVATE TARGETS ==============================#
_sync-all:
	uv sync --all-groups

_tools-install:
	uv tool install ruff -U

_hooks-install:
	printf '%s\n' '#!/bin/sh' 'make healthcheck' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

$(WHISPER_PROTO_DIR):
	mkdir -p $(WHISPER_PROTO_DIR)
#==============================================================================#
