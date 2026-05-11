.PHONY: help install lint test format clean run migrate

help:
	@echo "Publisher-v2 - Commandes:"
	@echo "  make install   - Installer dependances"
	@echo "  make lint      - Verifier code"
	@echo "  make test      - Lancer tests"
	@echo "  make run       - Lancer publisher local"
	@echo "  make migrate   - Voir les migrations SQL"
	@echo "  make clean     - Nettoyer caches"

install:
	pip install -r requirements.txt
	pip install pytest ruff mypy

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

run:
	PYTHONPATH=. python -m src.main

migrate:
	@echo "Migrations SQL a executer dans Supabase:"
	@echo ""
	@cat migrations/001_published_videos.sql
	@echo ""
	@cat migrations/002_upload_history.sql
