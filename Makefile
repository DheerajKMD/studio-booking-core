up:
	docker compose up --build

test:
	docker compose run --rm web pytest

lint:
	docker compose run --rm web sh -c "ruff check . && mypy ."