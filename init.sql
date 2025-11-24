-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Display enabled extensions
SELECT extname, extversion FROM pg_extension;
