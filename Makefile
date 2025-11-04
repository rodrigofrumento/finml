# Simple dev helpers
PY_DIR=backend
IMAGE?=finml-api
TAG?=dev
PORT?=8000

.PHONY: help
help:
	@echo "make venv        - create venv and install deps (local)"
	@echo "make run         - run uvicorn locally"
	@echo "make test        - run pytest"
	@echo "make fmt         - black + flake8"
	@echo "make docker      - build docker image"
	@echo "make up          - docker compose up (dev)"
	@echo "make down        - docker compose down"

venv:
	cd $(PY_DIR) && python -m venv .venv && \
	. .venv/bin/activate && pip install -U pip poetry && \
	poetry config virtualenvs.create false && poetry install

run:
	cd $(PY_DIR) && uvicorn app.main:app --reload --port $(PORT)

test:
	cd $(PY_DIR) && pytest -q

fmt:
	cd $(PY_DIR) && black . && flake8 .

docker:
	docker build -t $(IMAGE):$(TAG) $(PY_DIR)

up:
	docker compose -f docker-compose.dev.yml up --build

down:
	docker compose -f docker-compose.dev.yml down -v
