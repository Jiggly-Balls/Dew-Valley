all: ruff

ruff:
	uv run --dev ruff format
	uv run --dev ruff check --fix

check:
	uv run --dev basedpyright .