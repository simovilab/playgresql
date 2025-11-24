# PlaygreSQL

A development environment for testing PostgreSQL extensions (PostGIS, TimescaleDB, pgVector) using Django ORM with Python 3.14 and uv.

## Features

- **PostgreSQL 16** with PostGIS 3.4
- **Extensions**: PostGIS, TimescaleDB, pgVector
- **Python 3.14** with uv package manager
- **Django 5.2+** with PostGIS backend
- **Ollama** service for local LLM inference
- Hot-reload for development (code changes reflect immediately)
- Sample Django apps demonstrating extension usage

## Prerequisites

- Docker and Docker Compose
- uv (optional for local development)

## Quick Start

### 1. Start the containers

**Option A: Using the convenience script**

```bash
./start.sh
```

**Option B: Manual start**

```bash
docker compose up --build
```

This will:

- Build the PostgreSQL container with all extensions
- Build the Python/Django container
- Initialize the database with enabled extensions
- Start Django development server on http://localhost:8000
- Start Ollama service on http://localhost:11435

### 2. Access the database

**From your host machine:**

```bash
psql postgresql://postgres:postgres@localhost:5432/playgresql
```

**From the web container:**

```bash
docker compose exec web uv run python manage.py dbshell
```

### 3. Verify extensions

```bash
docker compose exec web uv run python manage.py shell
```

Then in the Python shell:

```python
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT extname, extversion FROM pg_extension;")
    for row in cursor.fetchall():
        print(row)
```

### 4. Access Ollama

The Ollama service is available at http://localhost:11435 (mapped to avoid conflicts with local Ollama instances).

From within the web container, use:
```bash
docker compose exec web uv run python manage.py shell
```

```python
import os
print(os.getenv('OLLAMA_HOST'))  # http://ollama:11434
```

Pull and run a model:
```bash
docker compose exec ollama ollama pull llama2
docker compose exec ollama ollama run llama2
```

## Testing Extensions

The repository includes `extensions_demo.py` with ready-to-use model examples for all three extensions. You can copy these models to your Django apps.

Two sample Django apps are included:
- `series/` - TimescaleDB time-series examples
- `vectors/` - pgVector embedding examples

### PostGIS Example

Create a Django app:

```bash
docker compose exec web uv run python manage.py startapp locations
```

Add to `config/settings.py` INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ...
    'locations',
]
```

Example model with PostGIS:

```python
# locations/models.py
from django.contrib.gis.db import models

class Place(models.Model):
    name = models.CharField(max_length=100)
    location = models.PointField()

    def __str__(self):
        return self.name
```

### TimescaleDB Example

Create a time-series model:

```python
from django.db import models

class SensorReading(models.Model):
    time = models.DateTimeField(primary_key=True)
    sensor_id = models.IntegerField()
    temperature = models.FloatField()
    humidity = models.FloatField()

    class Meta:
        db_table = 'sensor_readings'
```

Create hypertable via migration:

```python
from django.db import migrations

def create_hypertable(apps, schema_editor):
    schema_editor.execute(
        "SELECT create_hypertable('sensor_readings', 'time');"
    )

class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            "SELECT create_hypertable('sensor_readings', 'time');",
            reverse_sql="SELECT 1;"  # Cannot easily reverse
        ),
    ]
```

### pgVector Example

Create a vector embedding model:

```python
from django.db import models
from django.contrib.postgres.fields import ArrayField

class Document(models.Model):
    content = models.TextField()
    embedding = ArrayField(models.FloatField(), size=1536)  # e.g., OpenAI embeddings

    class Meta:
        db_table = 'documents'
```

Query similar vectors in Django shell:

```python
from django.db import connection

# Find similar documents using cosine distance
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT id, content, embedding <=> %s::vector AS distance
        FROM documents
        ORDER BY distance
        LIMIT 5
    """, [target_embedding])
```

## Development

### Local Python Setup

Install dependencies locally:

```bash
uv sync
```

Run migrations:

```bash
uv run python manage.py migrate
```

Create superuser:

```bash
docker compose exec web uv run python manage.py createsuperuser
```

### Database Management

**Reset database:**

```bash
docker compose down -v
docker compose up --build
```

**Run migrations:**

```bash
docker compose exec web uv run python manage.py migrate
```

**Create migrations:**

```bash
docker compose exec web uv run python manage.py makemigrations
```

### Direct PostgreSQL Access

```bash
docker compose exec db psql -U postgres -d playgresql
```

Test extensions:

```sql
-- PostGIS
SELECT PostGIS_version();

-- TimescaleDB
SELECT timescaledb_version();

-- pgVector
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Project Structure

```
.
├── playgresql/         # Django project settings
├── series/             # Sample TimescaleDB app
├── vectors/            # Sample pgVector app
├── manage.py           # Django management script
├── extensions_demo.py  # Example models for all extensions
├── start.sh            # Convenience startup script
├── Dockerfile          # PostgreSQL container
├── Dockerfile.python   # Python/Django container
├── docker-compose.yml  # Orchestration (includes Ollama)
├── init.sql           # Database initialization
├── pyproject.toml     # Python dependencies
├── .env.example       # Environment variables template
└── README.md
```

## Services and Ports

- **PostgreSQL**: port 5432
- **Django dev server**: port 8000
- **Ollama**: port 11435 (mapped from 11434 to avoid local conflicts)

## Environment Variables

See `.env.example` for available configuration options:
- `DATABASE_URL` - PostgreSQL connection string
- `ENABLE_GIS` - Enable/disable PostGIS features
- `OLLAMA_HOST` - Ollama service URL (set automatically in Docker)
- `DEBUG` - Django debug mode
- `SECRET_KEY` - Django secret key

## Notes

- Database and Ollama data persist in Docker volumes
- Code changes auto-reload in the web container
- This is a **development** environment (not production-ready)
- The `start.sh` script provides automated setup with health checks

## Troubleshooting

**Container won't start:**

```bash
docker compose logs
```

**Database connection issues:**

```bash
docker compose exec db pg_isready -U postgres
```

**Python dependencies not found:**

```bash
docker compose up --build
```
