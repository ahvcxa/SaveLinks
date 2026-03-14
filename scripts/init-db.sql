-- Enable the pg_trgm extension for GIN trigram indexes (used by ILIKE search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
