# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PlaygreSQL is a Docker-based development environment for testing PostgreSQL extensions (PostGIS, TimescaleDB, pgVector) using Django ORM with Python 3.14 and the `uv` package manager. This is a **development environment only** and is not production-ready.

## Architecture

### Multi-Container Setup

The project uses Docker Compose with three services:

1. **db (PostgreSQL 16)**: Custom-built container with PostGIS 3.4, TimescaleDB, and pgVector extensions pre-installed and enabled via `init.sql`
2. **web (Django 5.2+)**: Python 3.14 container running Django with hot-reload for development
3. **ollama**: LLM inference service for local AI experiments

### Django Configuration

- **Settings**: `playgresql/settings.py` conditionally loads PostGIS support based on `ENABLE_GIS` environment variable
- **Database Backend**: Automatically switches between `django.contrib.gis.db.backends.postgis` (when `ENABLE_GIS=true`) and `django.db.backends.postgresql`
- **Sample Apps**: `series/` and `vectors/` are empty Django apps for TimescaleDB and pgVector experimentation
- **Demo Models**: `extensions_demo.py` contains commented example models for all three extensions with usage patterns

### Extension-Specific Patterns

**PostGIS Models**:
- Use `from django.contrib.gis.db import models as gis_models`
- Fields: `PointField()`, `LineStringField()`, `PolygonField()`
- Requires `ENABLE_GIS=true` environment variable

**TimescaleDB Models**:
- Use regular Django models with `DateTimeField` as primary key
- Convert to hypertables via migration using `migrations.RunSQL("SELECT create_hypertable('table_name', 'time', if_not_exists => TRUE);")`
- Time-based queries leverage TimescaleDB's automatic optimizations

**pgVector Models**:
- Store embeddings using `ArrayField(models.FloatField(), size=DIMENSIONS)`
- Or use `pgvector.django.VectorField(dimensions=DIMENSIONS)` (as seen in `vectors/models.py`)
- Query with raw SQL using distance operators: `<=>` (cosine), `<->` (L2), `<#>` (inner product)

## Common Commands

### Container Management

Start all services:
```bash
./start.sh  # Automated with health checks and migrations
```

Or manually:
```bash
docker compose up --build
```

Stop and remove volumes (full reset):
```bash
docker compose down -v
```

### Django Operations

All Django commands must be prefixed with `docker compose exec web uv run`:

**Migrations**:
```bash
docker compose exec web uv run python manage.py makemigrations
docker compose exec web uv run python manage.py migrate
```

**Django Shell**:
```bash
docker compose exec web uv run python manage.py shell
```

**Create Superuser**:
```bash
docker compose exec web uv run python manage.py createsuperuser
```

**Create New App**:
```bash
docker compose exec web uv run python manage.py startapp <app_name>
```

Then add to `playgresql/settings.py` `INSTALLED_APPS`.

### Database Access

**From host machine**:
```bash
psql postgresql://postgres:postgres@localhost:5432/playgresql
```

**Django dbshell**:
```bash
docker compose exec web uv run python manage.py dbshell
```

**Direct psql**:
```bash
docker compose exec db psql -U postgres -d playgresql
```

### Verification Commands

**Check database health**:
```bash
docker compose exec db pg_isready -U postgres
```

**Verify extensions**:
```bash
docker compose exec db psql -U postgres -d playgresql -c "SELECT extname, extversion FROM pg_extension;"
```

**View logs**:
```bash
docker compose logs -f
docker compose logs -f web  # Django only
docker compose logs -f db   # PostgreSQL only
```

### Local Development (Optional)

Install dependencies locally without Docker:
```bash
uv sync
```

Run Django commands locally (requires local PostgreSQL):
```bash
uv run python manage.py migrate
```

Linting (ruff is in dev dependencies):
```bash
uv run ruff check .
```

### Ollama Usage

**Pull model**:
```bash
docker compose exec ollama ollama pull llama2
```

**Interactive session**:
```bash
docker compose exec ollama ollama run llama2
```

**From Django** (OLLAMA_HOST is pre-configured to `http://ollama:11434`):
```python
import os
print(os.getenv('OLLAMA_HOST'))
```

## Development Workflow

### Adding New Extension Features

1. Copy relevant model examples from `extensions_demo.py` to your app's `models.py`
2. Create migrations: `docker compose exec web uv run python manage.py makemigrations`
3. For TimescaleDB, add a second migration with `RunSQL` to create hypertables
4. For pgVector, add indexes via raw SQL migrations for optimal performance
5. Apply migrations: `docker compose exec web uv run python manage.py migrate`

### Working with TimescaleDB

After creating a time-series model, convert it to a hypertable in a migration:

```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('app_name', 'XXXX_previous_migration')]
    
    operations = [
        migrations.RunSQL(
            "SELECT create_hypertable('table_name', 'time', if_not_exists => TRUE);",
            reverse_sql="SELECT 1;"
        ),
    ]
```

### Working with pgVector

Create vector indexes after initial table creation:

```python
migrations.RunSQL(
    "CREATE INDEX ON table_name USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
    reverse_sql="DROP INDEX IF EXISTS table_name_embedding_idx;"
)
```

For similarity search, use raw SQL with distance operators in Django shell.

## Important Notes

- The web container has hot-reload enabled; code changes reflect immediately without restart
- Database and Ollama data persist in Docker volumes between restarts
- Ollama is mapped to port 11435 (not 11434) to avoid conflicts with local instances
- Use `ENABLE_GIS=true` environment variable to enable PostGIS features
- All credentials default to `postgres:postgres` for development convenience
- Never commit `.env` file (use `.env.example` as template)
