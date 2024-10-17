.PHONY: $(MAKECMDGOALS)

lint:
	@uv run ruff format .
	@uv run ruff check --fix .
	@uv run mypy .

lint-check:
	@uv run ruff check .
	@uv run mypy .

test:
	@uv run pytest -vv

run-local:
	@uv run uvicorn src.main:app --host 0.0.0.0 --port 5001 --reload

run-container:
	@docker-compose up --build -d

kill-container:
	@docker-compose down -t 1
