.PHONY: $(MAKECMDGOALS)

lint:
	@ruff format .
	@ruff check --fix .
	@mypy .

lint-check:
	@ruff check .
	@mypy .

test:
	@pytest -vv

run-local:
	@uvicorn src.main:app --host 0.0.0.0 --port 5001 --reload

run-container:
	@docker-compose up --build -d

kill-container:
	@docker-compose down -t 1
