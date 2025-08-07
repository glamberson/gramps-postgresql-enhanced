"""
PostgreSQL Enhanced - Search and AI Capabilities Module

Detects and manages available PostgreSQL extensions for:
- Full-text search
- Fuzzy/phonetic matching  
- Vector similarity (AI/ML)
- Graph queries (relationships)
"""

import logging
from typing import Dict, List, Set, Optional, Any
from enum import Enum, auto

LOG = logging.getLogger(__name__)


class ExtensionLevel(Enum):
    """Extension availability levels"""
    NONE = auto()        # Not available
    AVAILABLE = auto()   # Can be installed
    INSTALLED = auto()   # Ready to use
    CONFIGURED = auto()  # Fully configured with tables/indexes


class SearchCapabilities:
    """
    Detect and manage PostgreSQL extension capabilities.
    Provides tiered functionality based on what's available.
    """
    
    # Extension definitions with their features
    EXTENSIONS = {
        # Core search extensions
        'pg_trgm': {
            'description': 'Trigram similarity matching',
            'min_version': '1.4',
            'features': [
                'similarity',      # similarity(text, text) -> float
                'fuzzy_match',     # text % text operator
                'partial_match',   # LIKE with GIN index support
                'distance',        # <-> distance operator
            ],
            'sql_test': "SELECT 'test' % 'text'",
        },
        'fuzzystrmatch': {
            'description': 'Phonetic and string distance algorithms',
            'min_version': '1.1', 
            'features': [
                'soundex',         # soundex(text) -> text
                'metaphone',       # metaphone(text, max_length) -> text
                'dmetaphone',      # Double Metaphone
                'levenshtein',     # Edit distance
            ],
            'sql_test': "SELECT soundex('test')",
        },
        'unaccent': {
            'description': 'Remove accents from text',
            'min_version': '1.0',
            'features': [
                'unaccent',        # unaccent(text) -> text
                'accent_insensitive_search',
            ],
            'sql_test': "SELECT unaccent('café')",
        },
        'btree_gin': {
            'description': 'GIN indexes for common types',
            'min_version': '1.0',
            'features': [
                'multi_column_gin',  # Index (text, date, number) together
                'combined_search',   # Full-text + exact match
            ],
            'sql_test': None,  # No simple test
        },
        
        # AI/ML extensions
        'vector': {  # pgvector
            'description': 'Vector similarity search for AI/ML',
            'min_version': '0.5.0',
            'features': [
                'embeddings',      # Store text/image embeddings
                'cosine_similarity',  # <=> operator
                'euclidean_distance', # <-> operator  
                'inner_product',   # <#> operator
                'dna_matching',    # Custom: DNA segment vectors
                'face_vectors',    # Custom: Facial recognition vectors
                'document_similarity', # Custom: Document embeddings
            ],
            'sql_test': "SELECT '[1,2,3]'::vector",
            'sql_setup': """
                -- Example: DNA segment matching with pgvector
                CREATE TABLE IF NOT EXISTS dna_segments (
                    person_handle VARCHAR(50),
                    chromosome INTEGER,
                    start_position INTEGER,
                    end_position INTEGER,
                    segment_vector vector(128),  -- DNA characteristics as vector
                    centimorgan FLOAT,
                    snp_count INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_dna_vector 
                ON dna_segments USING ivfflat (segment_vector vector_cosine_ops);
            """
        },
        
        # Graph extensions
        'age': {  # Apache AGE
            'description': 'Graph database for relationship analysis',
            'min_version': '1.4.0',
            'features': [
                'cypher_queries',  # Graph query language
                'relationship_paths',  # Find all paths between people
                'common_ancestors',    # Find MRCAs
                'cousin_calculations', # Calculate exact relationships
                'descendant_trees',    # Full descendant graphs
                'pedigree_collapse',   # Detect same person in multiple places
                'cluster_analysis',    # Family group detection
            ],
            'sql_test': "SELECT * FROM ag_catalog.create_graph('test_graph')",
            'sql_setup': """
                -- Example: Create genealogy graph
                SELECT * FROM ag_catalog.create_graph('genealogy');
                
                -- Add person vertices and relationship edges
                -- This enables queries like:
                -- "Find all paths from person A to person B"
                -- "Find all cousins of degree N"
                -- "Detect pedigree collapse"
            """
        },
    }
    
    def __init__(self, dbapi):
        """Initialize capability detection"""
        self.dbapi = dbapi
        self.capabilities = {}
        self.search_level = 'basic'
        self._detect_capabilities()
    
    def _detect_capabilities(self):
        """Detect which extensions are available/installed"""
        with self.dbapi.execute("""
            SELECT 
                e.extname,
                e.extversion,
                x.default_version,
                CASE 
                    WHEN e.extname IS NOT NULL THEN 'installed'
                    WHEN x.name IS NOT NULL THEN 'available'
                    ELSE 'none'
                END as status
            FROM pg_available_extensions x
            LEFT JOIN pg_extension e ON x.name = e.extname
            WHERE x.name IN %s
        """, (tuple(self.EXTENSIONS.keys()),)) as cur:
            
            for row in cur.fetchall():
                ext_name = row[0] or row[2]  # Use name from either source
                self.capabilities[ext_name] = {
                    'status': row[3],
                    'installed_version': row[1],
                    'available_version': row[2],
                    'features': self.EXTENSIONS.get(ext_name, {}).get('features', [])
                }
        
        # Determine overall search level
        self._determine_search_level()
        
        # Log capabilities
        LOG.info(f"PostgreSQL Enhanced Capabilities: {self.search_level}")
        for ext, info in self.capabilities.items():
            LOG.debug(f"  {ext}: {info['status']}")
    
    def _determine_search_level(self):
        """Determine the search capability level"""
        installed = {
            ext for ext, info in self.capabilities.items() 
            if info['status'] == 'installed'
        }
        
        if 'age' in installed and 'vector' in installed:
            self.search_level = 'ai_graph'
        elif 'vector' in installed:
            self.search_level = 'ai_enabled'
        elif 'age' in installed:
            self.search_level = 'graph_enabled'
        elif {'pg_trgm', 'fuzzystrmatch', 'unaccent'}.issubset(installed):
            self.search_level = 'full'
        elif {'pg_trgm', 'fuzzystrmatch'}.issubset(installed):
            self.search_level = 'advanced'
        elif 'pg_trgm' in installed:
            self.search_level = 'enhanced'
        else:
            self.search_level = 'standard'  # Built-in full-text only
    
    def enable_extension(self, extension: str) -> bool:
        """
        Try to enable an extension if available.
        Returns True if successful.
        """
        if extension not in self.EXTENSIONS:
            LOG.warning(f"Unknown extension: {extension}")
            return False
        
        if self.capabilities.get(extension, {}).get('status') == 'installed':
            LOG.debug(f"Extension {extension} already installed")
            return True
        
        try:
            with self.dbapi.execute(f"CREATE EXTENSION IF NOT EXISTS {extension}"):
                pass
            
            LOG.info(f"Successfully enabled extension: {extension}")
            self.capabilities[extension]['status'] = 'installed'
            self._determine_search_level()
            return True
            
        except Exception as e:
            LOG.warning(f"Could not enable {extension}: {e}")
            return False
    
    def setup_search_infrastructure(self, mode: str = 'monolithic'):
        """
        Set up search infrastructure based on available extensions.
        Handles both separate and monolithic modes.
        """
        LOG.info(f"Setting up search infrastructure in {mode} mode")
        LOG.info(f"Search level: {self.search_level}")
        
        # Basic setup (always available)
        self._setup_basic_fulltext(mode)
        
        # Enhanced setups based on available extensions
        if 'pg_trgm' in self.get_installed_extensions():
            self._setup_trigram_search(mode)
        
        if 'fuzzystrmatch' in self.get_installed_extensions():
            self._setup_phonetic_search(mode)
        
        if 'vector' in self.get_installed_extensions():
            self._setup_vector_search(mode)
        
        if 'age' in self.get_installed_extensions():
            self._setup_graph_database(mode)
    
    def _setup_basic_fulltext(self, mode: str):
        """Set up basic full-text search (no extensions needed)"""
        # This works in both modes
        LOG.debug("Setting up basic full-text search")
        
        # Add search columns and indexes to each table
        # Implementation depends on mode (separate vs monolithic)
        pass
    
    def _setup_trigram_search(self, mode: str):
        """Set up trigram similarity search"""
        LOG.debug("Setting up trigram search with pg_trgm")
        
        # Create trigram indexes for fuzzy matching
        # Different table names based on mode
        pass
    
    def _setup_phonetic_search(self, mode: str):
        """Set up phonetic search functions"""
        LOG.debug("Setting up phonetic search with fuzzystrmatch")
        
        # Create functions for soundex, metaphone matching
        pass
    
    def _setup_vector_search(self, mode: str):
        """Set up vector similarity search for AI/ML features"""
        LOG.debug("Setting up vector search with pgvector")
        
        # Create tables for embeddings, DNA vectors, etc.
        if mode == 'monolithic':
            # Shared vector tables with tree prefixes
            sql = """
            CREATE TABLE IF NOT EXISTS dna_vectors (
                tree_id VARCHAR(50),
                person_handle VARCHAR(50),
                vector_type VARCHAR(20),  -- 'dna', 'face', 'document'
                embedding vector(512),
                metadata JSONB,
                PRIMARY KEY (tree_id, person_handle, vector_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_dna_embeddings 
            ON dna_vectors USING ivfflat (embedding vector_cosine_ops);
            """
        else:
            # Separate vector table per database
            sql = """
            CREATE TABLE IF NOT EXISTS person_vectors (
                person_handle VARCHAR(50) PRIMARY KEY,
                dna_embedding vector(256),
                face_embedding vector(512),
                document_embedding vector(768),
                metadata JSONB
            );
            """
        
        with self.dbapi.execute(sql):
            pass
    
    def _setup_graph_database(self, mode: str):
        """Set up Apache AGE graph database"""
        LOG.debug("Setting up graph database with Apache AGE")
        
        # Create graph for genealogy relationships
        if mode == 'monolithic':
            # One graph with tree-prefixed nodes
            graph_name = 'genealogy_unified'
        else:
            # Separate graph per tree
            graph_name = 'genealogy'
        
        try:
            with self.dbapi.execute(f"""
                SELECT * FROM ag_catalog.create_graph('{graph_name}')
            """):
                pass
            LOG.info(f"Created graph: {graph_name}")
        except Exception as e:
            LOG.debug(f"Graph may already exist: {e}")
    
    def get_installed_extensions(self) -> Set[str]:
        """Get set of installed extensions"""
        return {
            ext for ext, info in self.capabilities.items()
            if info['status'] == 'installed'
        }
    
    def get_available_features(self) -> List[str]:
        """Get list of all available features"""
        features = ['basic_search', 'fulltext_search']  # Always available
        
        for ext, info in self.capabilities.items():
            if info['status'] == 'installed':
                features.extend(info['features'])
        
        return features
    
    def can_do(self, feature: str) -> bool:
        """Check if a specific feature is available"""
        return feature in self.get_available_features()


class SearchAPI:
    """
    Unified search API that uses available capabilities.
    Works with both separate and monolithic modes.
    """
    
    def __init__(self, db, capabilities: SearchCapabilities):
        self.db = db
        self.capabilities = capabilities
    
    def search(self, 
               query: str,
               search_type: str = 'auto',
               **kwargs) -> List[Dict[str, Any]]:
        """
        Main search interface that adapts to available capabilities.
        
        Args:
            query: Search query
            search_type: 'auto', 'exact', 'fuzzy', 'phonetic', 'semantic'
            **kwargs: Additional parameters
        
        Returns:
            List of search results with relevance scores
        """
        if search_type == 'auto':
            # Choose best available search type
            if self.capabilities.can_do('embeddings'):
                return self.semantic_search(query, **kwargs)
            elif self.capabilities.can_do('fuzzy_match'):
                return self.fuzzy_search(query, **kwargs)
            else:
                return self.basic_search(query, **kwargs)
        
        # Dispatch to specific search method
        method_map = {
            'exact': self.basic_search,
            'fuzzy': self.fuzzy_search,
            'phonetic': self.phonetic_search,
            'semantic': self.semantic_search,
            'graph': self.graph_search,
        }
        
        method = method_map.get(search_type, self.basic_search)
        return method(query, **kwargs)
    
    def basic_search(self, query: str, **kwargs):
        """Basic search using LIKE or built-in full-text"""
        limit = kwargs.get('limit', 100)
        offset = kwargs.get('offset', 0)
        obj_types = kwargs.get('obj_types', ['person', 'family', 'event', 'place'])
        include_private = kwargs.get('include_private', True)
        
        results = []
        query_lower = query.lower()
        
        for obj_type in obj_types:
            table = self.db._get_table_name(obj_type)
            
            # Use PostgreSQL full-text search if available
            with self.db.dbapi.execute(f"""
                SELECT handle, gramps_id, json_data,
                       ts_rank_cd(
                           to_tsvector('simple', coalesce(json_data::text, '')),
                           plainto_tsquery('simple', %s)
                       ) as relevance
                FROM {table}
                WHERE to_tsvector('simple', coalesce(json_data::text, '')) 
                      @@ plainto_tsquery('simple', %s)
                ORDER BY relevance DESC
                LIMIT %s OFFSET %s
            """, (query, query, limit, offset)) as cur:
                for row in cur.fetchall():
                    results.append({
                        'handle': row[0],
                        'type': obj_type,
                        'gramps_id': row[1],
                        'data': row[2],
                        'relevance': float(row[3]) if row[3] else 0.5
                    })
        
        # Sort all results by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def fuzzy_search(self, query: str, **kwargs):
        """Fuzzy search using pg_trgm"""
        if not self.capabilities.can_do('fuzzy_match'):
            return self.basic_search(query, **kwargs)
        
        limit = kwargs.get('limit', 100)
        offset = kwargs.get('offset', 0)
        obj_types = kwargs.get('obj_types', ['person', 'family', 'event', 'place'])
        threshold = kwargs.get('threshold', 0.3)  # Similarity threshold
        
        results = []
        
        for obj_type in obj_types:
            table = self.db._get_table_name(obj_type)
            
            with self.db.dbapi.execute(f"""
                SELECT handle, gramps_id, json_data,
                       similarity(json_data::text, %s) as relevance
                FROM {table}
                WHERE json_data::text % %s  -- Trigram similarity operator
                   OR similarity(json_data::text, %s) > %s
                ORDER BY relevance DESC
                LIMIT %s OFFSET %s
            """, (query, query, query, threshold, limit, offset)) as cur:
                for row in cur.fetchall():
                    results.append({
                        'handle': row[0],
                        'type': obj_type,
                        'gramps_id': row[1],
                        'data': row[2],
                        'relevance': float(row[3])
                    })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def phonetic_search(self, query: str, **kwargs):
        """Phonetic search using fuzzystrmatch"""
        if not self.capabilities.can_do('soundex'):
            return self.fuzzy_search(query, **kwargs)
        
        limit = kwargs.get('limit', 100)
        offset = kwargs.get('offset', 0)
        obj_types = kwargs.get('obj_types', ['person'])  # Mainly for person names
        
        results = []
        
        for obj_type in obj_types:
            table = self.db._get_table_name(obj_type)
            
            # Use soundex for name matching
            with self.db.dbapi.execute(f"""
                SELECT handle, gramps_id, json_data,
                       difference(
                           coalesce(json_data->>'surname', ''),
                           %s
                       ) as relevance
                FROM {table}
                WHERE soundex(coalesce(json_data->>'surname', '')) = soundex(%s)
                   OR soundex(coalesce(json_data->>'given_name', '')) = soundex(%s)
                ORDER BY relevance DESC
                LIMIT %s OFFSET %s
            """, (query, query, query, limit, offset)) as cur:
                for row in cur.fetchall():
                    results.append({
                        'handle': row[0],
                        'type': obj_type,
                        'gramps_id': row[1],
                        'data': row[2],
                        'relevance': float(row[3]) / 4.0  # Normalize to 0-1
                    })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def semantic_search(self, query: str, **kwargs):
        """Semantic search using pgvector embeddings"""
        if not self.capabilities.can_do('embeddings'):
            return self.fuzzy_search(query, **kwargs)
        
        limit = kwargs.get('limit', 100)
        embedding_func = kwargs.get('embedding_function', None)
        
        if not embedding_func:
            LOG.warning("No embedding function provided, falling back to fuzzy search")
            return self.fuzzy_search(query, **kwargs)
        
        # Generate query embedding
        query_vector = embedding_func(query)
        vector_str = '[' + ','.join(map(str, query_vector)) + ']'
        
        results = []
        
        # Search in vector tables
        with self.db.dbapi.execute("""
            SELECT person_handle, vector_type, metadata,
                   1 - (embedding <=> %s::vector) as similarity
            FROM person_vectors
            WHERE 1 - (embedding <=> %s::vector) > 0.7
            ORDER BY similarity DESC
            LIMIT %s
        """, (vector_str, vector_str, limit)) as cur:
            for row in cur.fetchall():
                results.append({
                    'handle': row[0],
                    'type': 'person',
                    'vector_type': row[1],
                    'metadata': row[2],
                    'relevance': float(row[3])
                })
        
        return results
    
    def graph_search(self, query: str, **kwargs):
        """Graph queries using Apache AGE"""
        if not self.capabilities.can_do('cypher_queries'):
            raise NotImplementedError("Graph search requires Apache AGE")
        
        # Example Cypher query for finding relationships
        cypher = kwargs.get('cypher', None)
        if cypher:
            with self.db.dbapi.execute(f"""
                SELECT * FROM cypher('genealogy', $$
                    {cypher}
                $$) as (result agtype)
            """) as cur:
                results = []
                for row in cur.fetchall():
                    results.append({'result': row[0]})
                return results
        
        return []
    
    def find_relatives(self, person_handle: str, 
                      relationship_type: str = 'all',
                      max_depth: int = 5):
        """Find relatives using graph queries if available"""
        if self.capabilities.can_do('relationship_paths'):
            # Use Apache AGE for efficient path finding
            return self._graph_relatives(person_handle, relationship_type, max_depth)
        else:
            # Fall back to recursive SQL or application logic
            return self._sql_relatives(person_handle, relationship_type, max_depth)
    
    def find_dna_matches(self, person_handle: str,
                        min_cm: float = 7.0,
                        min_snps: int = 500):
        """Find DNA matches using vector similarity if available"""
        if self.capabilities.can_do('dna_matching'):
            # Use pgvector for DNA segment matching
            return self._vector_dna_matches(person_handle, min_cm, min_snps)
        else:
            # Fall back to traditional SQL matching
            return self._sql_dna_matches(person_handle, min_cm, min_snps)