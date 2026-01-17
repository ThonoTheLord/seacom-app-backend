-- Run this AFTER creating the database
-- Connect to seacom_experimental_db first, then run:

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable PostGIS topology (optional, for network topology)
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable fuzzy string matching (useful for search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify PostGIS is installed
SELECT PostGIS_Full_Version();

-- You should see something like:
-- "POSTGIS="3.4.0" GEOS="3.12.0" PROJ="9.3.0" ..."
