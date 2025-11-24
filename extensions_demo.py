"""
Sample models demonstrating PostgreSQL extensions usage with Django ORM.

This file contains example models for PostGIS, TimescaleDB, and pgVector.
Copy the relevant models to your Django app's models.py file.

Note: Make sure to enable ENABLE_GIS=true for PostGIS models.
"""

# ============================================================================
# PostGIS Examples
# ============================================================================

# Uncomment when ENABLE_GIS is enabled
# from django.contrib.gis.db import models as gis_models
# from django.db import models

# class Place(gis_models.Model):
#     """Example model using PostGIS point geometry."""
#     name = models.CharField(max_length=200)
#     location = gis_models.PointField()
#     description = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'places'
#
#     def __str__(self):
#         return self.name

# class Route(gis_models.Model):
#     """Example model using PostGIS line geometry."""
#     name = models.CharField(max_length=200)
#     path = gis_models.LineStringField()
#     distance_km = models.FloatField(null=True, blank=True)
#
#     class Meta:
#         db_table = 'routes'
#
#     def __str__(self):
#         return self.name

# class Region(gis_models.Model):
#     """Example model using PostGIS polygon geometry."""
#     name = models.CharField(max_length=200)
#     boundary = gis_models.PolygonField()
#     area_sq_km = models.FloatField(null=True, blank=True)
#
#     class Meta:
#         db_table = 'regions'
#
#     def __str__(self):
#         return self.name


# ============================================================================
# TimescaleDB Example
# ============================================================================

from django.db import models


class SensorReading(models.Model):
    """
    Example time-series model for TimescaleDB.

    After creating this model and running migrations, convert it to a hypertable:

    CREATE EXTENSION IF NOT EXISTS timescaledb;
    SELECT create_hypertable('sensor_readings', 'time');

    Or via Django migration:

    from django.db import migrations

    class Migration(migrations.Migration):
        dependencies = [('your_app', 'XXXX_previous_migration')]

        operations = [
            migrations.RunSQL(
                "SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);",
                reverse_sql="SELECT 1;"
            ),
        ]
    """

    time = models.DateTimeField(primary_key=True)
    sensor_id = models.CharField(max_length=50, db_index=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "sensor_readings"
        ordering = ["-time"]
        indexes = [
            models.Index(fields=["sensor_id", "time"]),
        ]

    def __str__(self):
        return f"{self.sensor_id} at {self.time}"


class MetricData(models.Model):
    """
    Another time-series example for application metrics.

    Convert to hypertable:
    SELECT create_hypertable('metric_data', 'timestamp');
    """

    timestamp = models.DateTimeField(primary_key=True)
    metric_name = models.CharField(max_length=100, db_index=True)
    value = models.FloatField()
    tags = models.JSONField(default=dict)

    class Meta:
        db_table = "metric_data"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}: {self.value} at {self.timestamp}"


# ============================================================================
# pgVector Example
# ============================================================================

from django.contrib.postgres.fields import ArrayField


class Document(models.Model):
    """
    Example model using pgVector for semantic search.

    The embedding field stores vector embeddings (e.g., from OpenAI, sentence-transformers).

    To create a vector index for efficient similarity search:

    CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

    Or for HNSW index (faster but more memory):

    CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

    Query similar documents:

    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id, title, embedding <=> %s::vector AS distance
            FROM documents
            ORDER BY distance
            LIMIT 10
        ''', [query_embedding])
        results = cursor.fetchall()
    """

    title = models.CharField(max_length=500)
    content = models.TextField()
    # Store embeddings as float array (e.g., 1536 dimensions for OpenAI text-embedding-3-small)
    embedding = ArrayField(models.FloatField(), size=1536, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ImageEmbedding(models.Model):
    """
    Example model for image embeddings using pgVector.

    Useful for image similarity search, reverse image search, etc.
    """

    image_url = models.URLField()
    embedding = ArrayField(models.FloatField(), size=512, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "image_embeddings"

    def __str__(self):
        return self.image_url


# ============================================================================
# Usage Examples in Django Shell
# ============================================================================

"""
# PostGIS Examples (when ENABLE_GIS=true)
# ----------------------------------------

from django.contrib.gis.geos import Point, LineString, Polygon
from extensions_demo import Place, Route, Region

# Create a place
place = Place.objects.create(
    name="San Francisco",
    location=Point(-122.4194, 37.7749),
    description="City in California"
)

# Find places within 10km of a point
from django.contrib.gis.measure import D
nearby = Place.objects.filter(
    location__distance_lte=(Point(-122.4, 37.7), D(km=10))
)

# Find places within a polygon
from django.contrib.gis.geos import Polygon
bbox = Polygon.from_bbox((-123, 37, -122, 38))
in_bbox = Place.objects.filter(location__within=bbox)


# TimescaleDB Examples
# --------------------

from datetime import datetime, timedelta
from extensions_demo import SensorReading

# Insert sensor readings
SensorReading.objects.create(
    time=datetime.now(),
    sensor_id="temp_01",
    temperature=22.5,
    humidity=65.0
)

# Time-based queries (leveraging TimescaleDB optimizations)
recent = SensorReading.objects.filter(
    time__gte=datetime.now() - timedelta(hours=1)
)

# Aggregations by sensor
from django.db.models import Avg
avg_temp = SensorReading.objects.filter(
    sensor_id="temp_01"
).aggregate(Avg('temperature'))

# Use raw SQL for TimescaleDB-specific functions
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('''
        SELECT time_bucket('1 hour', time) AS hour,
               sensor_id,
               AVG(temperature) as avg_temp
        FROM sensor_readings
        WHERE time > NOW() - INTERVAL '1 day'
        GROUP BY hour, sensor_id
        ORDER BY hour DESC
    ''')
    results = cursor.fetchall()


# pgVector Examples
# -----------------

from extensions_demo import Document
import numpy as np

# Create document with embedding
# (In real use, generate embedding using OpenAI, sentence-transformers, etc.)
embedding = np.random.rand(1536).tolist()

doc = Document.objects.create(
    title="Introduction to PostgreSQL",
    content="PostgreSQL is a powerful open-source database...",
    embedding=embedding
)

# Find similar documents
from django.db import connection

query_embedding = np.random.rand(1536).tolist()

with connection.cursor() as cursor:
    # Cosine similarity search
    cursor.execute('''
        SELECT id, title, embedding <=> %s::vector AS distance
        FROM documents
        WHERE embedding IS NOT NULL
        ORDER BY distance
        LIMIT 5
    ''', [query_embedding])
    
    similar_docs = cursor.fetchall()
    for doc_id, title, distance in similar_docs:
        print(f"{title}: {distance:.4f}")

# For L2 distance, use <-> operator
# For inner product, use <#> operator
"""
