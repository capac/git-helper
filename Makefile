# ── git-helper Makefile ───────────────────────────────────────────────────────
# Usage: make <target>
# Run `make help` to see all available targets.

.DEFAULT_GOAL := help
.PHONY: help install sync app ingest ingest-schedule \
        monitoring-up monitoring-down monitoring-logs

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
	@echo "    sync             Sync dependencies from pyproject.toml"
	@echo ""
	@echo "  App"
	@echo "    app              Run the Streamlit app locally"
	@echo ""
	@echo "  Ingestion"
	@echo "    ingest           Run the Prefect ingestion pipeline once"
	@echo "    ingest-schedule  Run the pipeline on a weekly schedule"
	@echo ""
	@echo "  Monitoring"
	@echo "    monitoring-up    Start PostgreSQL + Grafana via docker-compose"
	@echo "    monitoring-down  Stop and remove monitoring containers"
	@echo "    monitoring-logs  Tail logs from monitoring containers"
	@echo ""
	@echo "  Misc"
	@echo "    clean            Remove __pycache__, .pytest_cache, build artefacts"
	@echo ""

# Setup
install:
	uv sync --all-extras
	@echo "Environment ready."

sync:
	uv sync
	@echo "Dependencies synced."

# App
app:
	$(STREAMLIT) run app/streamlit_app.py

# Ingestion
ingest:
	$(PYTHON) ingest/pipeline.py

ingest-schedule:
	$(PYTHON) ingest/pipeline.py --schedule

# Monitoring
monitoring-up:
	docker-compose -f monitoring/docker-compose.yml up -d
	@echo "PostgreSQL running at localhost:5432"
	@echo "Grafana running at http://localhost:3000  (admin / admin)"

monitoring-down:
	docker-compose -f monitoring/docker-compose.yml down

monitoring-logs:
	docker-compose -f monitoring/docker-compose.yml logs -f

# Misc
clean:
	find . -type d -name "__pycache__"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info"    -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"         -delete 2>/dev/null || true
	@echo "Cleaned."
