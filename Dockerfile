FROM postgis/postgis:16-3.4

# Install TimescaleDB and pgvector
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-16-timescaledb \
    postgresql-16-pgvector && \
    rm -rf /var/lib/apt/lists/*

# Configure PostgreSQL to preload TimescaleDB
RUN echo "shared_preload_libraries = 'timescaledb'" >> /usr/share/postgresql/postgresql.conf.sample
