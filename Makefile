.PHONY: install test run up down lint backtest retrain drift load k8s-apply

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

backtest:
	python3 scripts/backtest_replay.py --input data/sample_events.json --api-url http://localhost:8000 --speed 5

retrain:
	python3 scripts/retrain.py --dataset data/labeled_sample.csv --model-name svm_market_abuse

drift:
	python3 scripts/drift_monitor.py --baseline data/baseline_features.csv --current data/current_features.csv --psi-threshold 0.25

load:
	locust -f scripts/load/locustfile.py --host http://localhost:8000

k8s-apply:
	kubectl apply -f k8s/base
