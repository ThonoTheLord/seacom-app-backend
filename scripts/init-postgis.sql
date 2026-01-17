-- Initialize PostGIS extensions for Seacom Experimental Database

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable PostGIS topology (optional, for network topology)
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable fuzzy string matching (useful for search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify PostGIS is installed
SELECT PostGIS_Version();

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostGIS extensions initialized successfully for Seacom Experimental DB';
END $$;
