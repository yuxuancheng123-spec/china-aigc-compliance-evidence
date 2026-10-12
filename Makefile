.PHONY: install test validate demo

install:
	pip install -r requirements.txt pytest

test:
	python -m pytest -q

validate:
	python -m src.validator

demo:
	python -m src.demo
