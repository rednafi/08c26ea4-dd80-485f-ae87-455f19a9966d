.PHONY: $(MAKECMDGOALS) # Avoid conflicts with files in the directory

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
	@tar \
    	--exclude='.venv' \
    	--exclude='.pytest_cache' \
    	--exclude='.mypy_cache' \
    	--exclude='.ruff_cache' \
    	--exclude='.git' \
    	--exclude='.vscode' \
    	--exclude='.coverage' \
    	--exclude="*/__pycache__" \
		--exclude=".DS_Store" \
		--exclude="*/.DS_Store" \
		--exclude=".tar" \
		--exclude="pipeline" \
    	-cvf pipeline.tar .


unarchive: ## Extract the tarball of the project
	@mkdir -p ./pipeline
	@tar -xvf pipeline.tar -C ./pipeline
