.PHONY: test lint up down helm
test: ; cd services/api && pip install -q -r requirements.txt && pytest -q
lint: ; ruff check services
up:   ; docker compose up -d --build --scale worker=2
down: ; docker compose down
helm: ; helm lint helm/taskforge
