# ── git-helper Makefile ───────────────────────────────────────────────────────
# Usage: make <target>
# Run `make help` to see all available targets.

.DEFAULT_GOAL := help
.PHONY: help install sync app ingest \
        monitoring-up monitoring-down

# Variables
PYTHON      := uv run python
STREAMLIT   := uv run streamlit

# Help
help:
	@echo ""
	@echo "  git-helper — available targets"
	@echo "  ────────────────────────────────────────────────────"
	@echo ""
	@echo "  Setup"
	@echo "    install          Create virtualenv and install all dependencies"
	@echo ""
	@echo "  App"
	@echo "    app              Run the Streamlit app locally"
	@echo ""
	@echo "  Ingestion"
	@echo "    ingest           Run the Prefect ingestion pipeline once"
	@echo ""
	@echo "  Monitoring"
	@echo "    monitoring-up    Start PostgreSQL and Grafana via docker-compose"
	@echo "    monitoring-down  Stop and remove monitoring containers"
	@echo ""
	@echo "  Misc"
	@echo "    clean            Remove __pycache__, .pytest_cache and build artefacts"
	@echo ""

# Setup
install:
	uv sync --all-extras
	@echo "Environment ready."

# App
app:
	$(STREAMLIT) run app/streamlit_app.py

# Ingestion
ingest:
	$(PYTHON) ingest/run.py

# Monitoring
monitoring-up:
	docker-compose -f monitoring/docker-compose.yml up -d
	@echo "PostgreSQL running at localhost:5432"
	@echo "Grafana running at http://localhost:3000  (admin / admin)"

monitoring-down:
	docker-compose -f monitoring/docker-compose.yml down

# Misc
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."
