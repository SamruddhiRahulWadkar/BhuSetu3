# BhuSetu: Makefile for SIH 26018 Hackathon Prototype

.PHONY: all setup test evaluate run-backend run-frontend demo clean

all: demo

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

test:
	.venv/bin/pytest backend/tests -v

evaluate:
	.venv/bin/python -m backend.app.analytics.evaluate

demo:
	.venv/bin/python demo.py

run-backend:
	.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

run-all:
	@echo "Starting BhuSetu Backend and Frontend..."
	$(MAKE) -j 2 run-backend run-frontend

clean:
	rm -rf __pycache__ .pytest_cache
