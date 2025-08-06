# PostgreSQL Extensions Roadmap for Gramps

## Core Extensions for Genealogy

### 1. Apache AGE (Graph Database) 🔥
**Use Case**: Relationship path finding, ancestry visualization, complex relationship queries

```sql
-- Enable Apache AGE
CREATE EXTENSION age;
LOAD 'age';

-- Create graph schema
SELECT create_graph('genealogy_graph');

-- Example: Find relationship path between two people
SELECT * FROM cypher('genealogy_graph', $$
    MATCH path = shortestPath(
        (p1:Person {gramps_id: 'I0001'})-[*]-(p2:Person {gramps_id: 'I0042'})
    )
    RETURN path, length(path) as distance
$$) as (path agtype, distance int);

-- Find all ancestors
SELECT * FROM cypher('genealogy_graph', $$
    MATCH (p:Person {gramps_id: 'I0001'})-[:CHILD_OF*]->(ancestor:Person)
    RETURN DISTINCT ancestor.gramps_id, ancestor.name
    ORDER BY ancestor.birth_date
$$) as (gramps_id text, name text);
```

**Implementation Plan**:
```python
class GraphQueries:
    """Apache AGE graph queries for relationships."""
    
    def sync_to_graph(self):
        """Sync JSONB data to graph nodes/edges."""
        # Create Person nodes
        self.execute("""
            SELECT * FROM cypher('genealogy_graph', $$
                MERGE (p:Person {
                    handle: %s,
                    gramps_id: %s,
                    name: %s,
                    birth_date: %s
                })
            $$) as (v agtype)
        """, [handle, gramps_id, name, birth_date])
        
        # Create CHILD_OF relationships
        for family in families:
            for parent in family.parents:
                for child in family.children:
                    self.execute_graph("""
                        MATCH (c:Person {handle: %s}), (p:Person {handle: %s})
                        MERGE (c)-[:CHILD_OF]->(p)
                    """, [child_handle, parent_handle])
```

### 2. pgvector (AI/ML Vector Similarity) 🧬
**Use Case**: DNA matching, photo similarity, descendant prediction

```sql
-- Enable pgvector
CREATE EXTENSION vector;

-- Add DNA embedding column
ALTER TABLE person ADD COLUMN dna_embedding vector(768);
ALTER TABLE person ADD COLUMN photo_embedding vector(512);

-- Find DNA matches
SELECT 
    p2.gramps_id,
    p2.json_data->>'name' as name,
    1 - (p1.dna_embedding <=> p2.dna_embedding) as similarity
FROM person p1, person p2
WHERE p1.gramps_id = 'I0001'
  AND p1.dna_embedding IS NOT NULL
  AND p2.dna_embedding IS NOT NULL
  AND p1.handle != p2.handle
  AND 1 - (p1.dna_embedding <=> p2.dna_embedding) > 0.95
ORDER BY similarity DESC;

-- Find similar photos
CREATE INDEX idx_photo_embedding ON person 
USING ivfflat (photo_embedding vector_cosine_ops)
WITH (lists = 100);
```

**Implementation**:
```python
class AIQueries:
    """AI-powered queries using pgvector."""
    
    def store_dna_embedding(self, handle, dna_data):
        """Convert DNA data to vector embedding."""
        # Use a DNA-to-vector model (e.g., via API)
        embedding = self.dna_to_vector(dna_data)
        self.execute("""
            UPDATE person 
            SET dna_embedding = %s::vector
            WHERE handle = %s
        """, [embedding.tolist(), handle])
    
    def find_genetic_matches(self, handle, threshold=0.9):
        """Find potential genetic relatives."""
        return self.execute("""
            WITH target AS (
                SELECT dna_embedding FROM person WHERE handle = %s
            )
            SELECT 
                p.handle,
                p.json_data,
                1 - (p.dna_embedding <=> t.dna_embedding) as match_score
            FROM person p, target t
            WHERE p.dna_embedding IS NOT NULL
              AND 1 - (p.dna_embedding <=> t.dna_embedding) > %s
            ORDER BY match_score DESC
        """, [handle, threshold])
```

### 3. PostGIS (Geographical Analysis) 🗺️
**Use Case**: Migration patterns, place clustering, geographical ancestry

```sql
-- Enable PostGIS
CREATE EXTENSION postgis;

-- Add geometry columns
ALTER TABLE place ADD COLUMN location geometry(Point, 4326);
ALTER TABLE person ADD COLUMN birth_location geometry(Point, 4326);

-- Update from lat/long
UPDATE place 
SET location = ST_SetSRID(
    ST_MakePoint(
        (json_data->>'longitude')::float,
        (json_data->>'latitude')::float
    ), 4326
)
WHERE json_data->>'longitude' IS NOT NULL;

-- Find migration patterns
WITH person_places AS (
    SELECT 
        p.handle,
        pl.location as birth_place,
        ST_Distance(pl.location, pl2.location) as migration_distance
    FROM person p
    JOIN place pl ON p.json_data->>'birth_place' = pl.handle
    JOIN place pl2 ON p.json_data->>'death_place' = pl2.handle
)
SELECT 
    AVG(migration_distance) as avg_migration,
    MAX(migration_distance) as max_migration
FROM person_places;
```

### 4. Full Text Search (Built-in) 🔍
**Use Case**: Search across all text fields

```sql
-- Add FTS column
ALTER TABLE person ADD COLUMN search_vector tsvector;

-- Update search vector
UPDATE person SET search_vector = 
    to_tsvector('english', 
        COALESCE(json_data->>'gramps_id', '') || ' ' ||
        COALESCE(json_data#>>'{names,0,first_name}', '') || ' ' ||
        COALESCE(json_data#>>'{names,0,surname,surname}', '') || ' ' ||
        COALESCE(json_data->>'occupation', '')
    );

-- Create GIN index
CREATE INDEX idx_person_fts ON person USING GIN(search_vector);

-- Search
SELECT * FROM person 
WHERE search_vector @@ plainto_tsquery('english', 'carpenter boston');
```

### 5. TimescaleDB (Time-Series Analysis) ⏰
**Use Case**: Historical analysis, family timeline visualization

```sql
-- Enable TimescaleDB
CREATE EXTENSION timescaledb;

-- Create events hypertable
CREATE TABLE person_events (
    time TIMESTAMPTZ NOT NULL,
    person_handle TEXT,
    event_type TEXT,
    event_data JSONB
);

SELECT create_hypertable('person_events', 'time');

-- Analyze family patterns over time
SELECT 
    time_bucket('10 years', time) AS decade,
    COUNT(*) FILTER (WHERE event_type = 'birth') as births,
    COUNT(*) FILTER (WHERE event_type = 'death') as deaths,
    COUNT(*) FILTER (WHERE event_type = 'marriage') as marriages
FROM person_events
WHERE time > '1800-01-01'
GROUP BY decade
ORDER BY decade;
```

## Implementation Architecture

```python
class PostgreSQLEnhanced(DBAPI):
    def __init__(self):
        super().__init__()
        self.extensions = {
            'age': GraphExtension(self),
            'vector': VectorExtension(self),
            'postgis': SpatialExtension(self),
            'fts': FullTextExtension(self),
            'timescale': TimeSeriesExtension(self)
        }
    
    def enable_extension(self, name):
        """Enable and initialize an extension."""
        if name in self.extensions:
            self.extensions[name].enable()
            self.extensions[name].initialize_schema()
```

## Schema Design for Extensions

```sql
-- Main tables remain DBAPI-compatible
CREATE TABLE person (
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB NOT NULL,
    -- GENERATED columns for DBAPI
    gramps_id VARCHAR(50) GENERATED ALWAYS AS (json_data->>'gramps_id') STORED,
    
    -- Extension columns (nullable, no impact if not used)
    -- Apache AGE
    graph_node_id BIGINT,
    
    -- pgvector
    dna_embedding vector(768),
    photo_embedding vector(512),
    
    -- PostGIS
    birth_location geometry(Point, 4326),
    
    -- Full Text Search
    search_vector tsvector,
    
    -- Indexes
    CONSTRAINT person_gramps_id_idx UNIQUE (gramps_id)
);

-- Extension-specific tables
CREATE TABLE graph_sync_log (
    handle VARCHAR(50),
    synced_at TIMESTAMP,
    sync_type VARCHAR(50)
);
```

## Future Extensions to Consider

1. **pg_similarity** - Name matching, fuzzy search
2. **plpython3u** - Python stored procedures for complex algorithms
3. **pg_cron** - Scheduled tasks (sync, cleanup)
4. **pgaudit** - Audit trail for genealogy changes
5. **pg_stat_statements** - Query performance analysis

## Benefits

1. **Graph queries** - "How am I related to X?" in milliseconds
2. **DNA matching** - Find genetic relatives instantly
3. **Geographic analysis** - Track migration patterns
4. **AI-powered search** - Similar names, photos, patterns
5. **Time series** - Analyze family trends over centuries

This makes Gramps PostgreSQL Enhanced the most advanced genealogy database available!