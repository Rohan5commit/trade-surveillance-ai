.PHONY: install test run up down lint

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m pytest

run:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

up:
	docker compose up --build

down:
	docker compose down

lint:
	python3 -m compileall src
