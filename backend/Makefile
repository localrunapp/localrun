.PHONY: help install dev test lint format clean run

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install dev dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean cache files"
	@echo "  make run        - Run application"

install:
	pipenv install

dev:
	pipenv install --dev

test:
	pipenv run pytest

lint:
	pipenv run ruff check .

format:
	pipenv run ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf storage/cache/*

run:
	pipenv run python main.py
