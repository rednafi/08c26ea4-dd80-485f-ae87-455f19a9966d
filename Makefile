.PHONY: $(MAKECMDGOALS)

lint:
	@uv run ruff format .
	@uv run ruff check --fix .
	@uv run mypy .

lint-check:
	@uv run ruff check .
	@uv run mypy .

test:
	@uv run pytest -vv -k 'not integration'

test-integration:
	@uv run pytest -vv -k 'integration'

run-local:
	@uv run uvicorn src.main:app --host 0.0.0.0 --port 5001 --reload

run-container:
	@docker-compose up --build -d

kill-container:
	@docker-compose down -t 1

archive: ## Create a tarball of the project
	@tar -czvf src.tar.gz src

unarchive: ## Extract the tarball of the project
	@tar -xzvf src.tar.gz
