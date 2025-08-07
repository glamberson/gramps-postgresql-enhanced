"""
PostgreSQL Native Search Indexer for Gramps Web

Replaces sifts library with native PostgreSQL search.
No psycopg2 dependency - uses psycopg3 through PostgreSQL Enhanced.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set
from gramps.gen.db.base import DbReadBase

LOG = logging.getLogger(__name__)


class PostgreSQLSearchIndexer:
    """
    Native PostgreSQL search indexer for Gramps Web.
    Drop-in replacement for sifts-based indexer.
    """
    
    SUFFIX = ""
    SUFFIX_PUBLIC = "__p"
    
    def __init__(
        self,
        tree: str,
        db_url: Optional[str] = None,
        embedding_function: Callable | None = None,
        use_fts: bool = True,
        use_semantic_text: bool = False,
    ):
        """Initialize the PostgreSQL native indexer."""
        if not tree:
            raise ValueError("`tree` is required for the search index")
        if tree.endswith("__p") or tree.endswith("__s"):
            raise ValueError("Invalid tree ID")
        
        self.tree = tree
        self.use_semantic_text = use_semantic_text
        self.use_fts = use_fts
        self.embedding_function = embedding_function
        self.db = None  # Will be set when database is provided
        
        LOG.info(f"PostgreSQL Native Search Indexer initialized for tree: {tree}")
    
    def set_database(self, db):
        """Set the database backend (PostgreSQL Enhanced)"""
        self.db = db
        
        # Check if database has native search capabilities
        if hasattr(db, 'search_api') and db.search_api:
            LOG.info("Using PostgreSQL Enhanced native search capabilities")
            self.has_native_search = True
        else:
            LOG.warning("Database doesn't have native search, using fallback")
            self.has_native_search = False
    
    def count(self, include_private: bool) -> int:
        """Return the number of searchable items."""
        if not self.db:
            return 0
        
        # Count objects in database
        total = 0
        for obj_type in ['person', 'family', 'event', 'place', 'source']:
            func = getattr(self.db, f'get_number_of_{obj_type}s', None)
            if func:
                total += func()
        
        return total
    
    def reindex_full(
        self, db_handle: DbReadBase, progress_cb: Optional[Callable] = None
    ):
        """
        Setup PostgreSQL full-text search indexes.
        Unlike sifts, we don't need to extract and store text separately.
        """
        LOG.info("Setting up PostgreSQL native full-text search indexes")
        
        if not self.db:
            self.set_database(db_handle)
        
        # If database has setup_fulltext_search method, use it
        if hasattr(self.db, 'setup_fulltext_search'):
            self.db.setup_fulltext_search()
            LOG.info("Full-text search indexes created successfully")
        else:
            LOG.warning("Database doesn't support native full-text search setup")
        
        # Report progress
        if progress_cb:
            total = self.count(include_private=True)
            progress_cb(current=total, total=total)
    
    def reindex_incremental(
        self, db_handle: DbReadBase, progress_cb: Optional[Callable] = None
    ):
        """
        PostgreSQL automatically updates search vectors via triggers.
        No manual incremental indexing needed.
        """
        LOG.debug("PostgreSQL search vectors update automatically via triggers")
        
        # Just report completion
        if progress_cb:
            progress_cb(current=1, total=1)
    
    def delete_object(self, handle: str, class_name: str) -> None:
        """
        No action needed - PostgreSQL cascades deletions automatically.
        """
        LOG.debug(f"Object {class_name}:{handle} will be removed from search on deletion")
    
    def add_or_update_object(
        self, handle: str, db_handle: DbReadBase, class_name: str
    ) -> None:
        """
        No action needed - PostgreSQL triggers update search vectors automatically.
        """
        LOG.debug(f"Object {class_name}:{handle} search vector updated via trigger")
    
    @staticmethod
    def _format_hit(hit: Dict[str, Any], rank: int, include_content: bool) -> Dict[str, Any]:
        """Format a search hit for Gramps Web API."""
        formatted_hit = {
            "handle": hit.get("handle"),
            "object_type": hit.get("type", hit.get("object_type")),
            "score": hit.get("relevance", hit.get("score", 1.0)),
            "rank": rank,
        }
        if include_content and "data" in hit:
            formatted_hit["content"] = hit.get("data", "")
        return formatted_hit
    
    def search(
        self,
        query: str,
        page: int,
        pagesize: int,
        include_private: bool = True,
        sort: Optional[List[str]] = None,
        object_types: Optional[List[str]] = None,
        change_op: Optional[str] = None,
        change_value: Optional[float] = None,
        include_content: bool = False,
    ):
        """
        Search using PostgreSQL native full-text search.
        
        This method provides the same interface as sifts for compatibility
        but uses PostgreSQL's native search capabilities.
        """
        if not self.db:
            LOG.error("Database not set for search indexer")
            return 0, []
        
        # Use native search if available
        if self.has_native_search and hasattr(self.db, 'search'):
            offset = (page - 1) * pagesize
            
            # Determine search type based on query
            search_type = 'fulltext'
            if query and query.strip() != "*":
                # Check for special search syntax
                if query.startswith("~"):  # Fuzzy search
                    search_type = 'fuzzy'
                    query = query[1:].strip()
                elif query.startswith("@"):  # Phonetic search
                    search_type = 'soundex'
                    query = query[1:].strip()
                elif self.use_semantic_text and self.embedding_function:
                    search_type = 'semantic'
            
            # Perform search
            try:
                results = self.db.search(
                    query=query,
                    search_type=search_type,
                    obj_types=object_types,
                    limit=pagesize,
                    offset=offset,
                    include_private=include_private
                )
                
                # Format results for Gramps Web API
                hits = []
                for i, result in enumerate(results):
                    hit = self._format_hit(result, rank=offset + i, include_content=include_content)
                    hits.append(hit)
                
                # Estimate total (PostgreSQL doesn't always give exact count efficiently)
                total = len(results) + offset if len(results) == pagesize else offset + len(results)
                
                return total, hits
                
            except Exception as e:
                LOG.error(f"Search failed: {e}")
                return 0, []
        
        # Fallback to basic search
        return self._basic_search_fallback(
            query, page, pagesize, include_private, object_types, include_content
        )
    
    def _basic_search_fallback(
        self,
        query: str,
        page: int,
        pagesize: int,
        include_private: bool,
        object_types: Optional[List[str]],
        include_content: bool
    ):
        """
        Basic search fallback when native search is not available.
        Uses LIKE queries on JSONB data.
        """
        LOG.debug("Using basic search fallback")
        
        if not object_types:
            object_types = ['person', 'family', 'event', 'place', 'source']
        
        offset = (page - 1) * pagesize
        results = []
        
        # Search each object type
        for obj_type in object_types:
            if obj_type == 'person':
                # Search persons by name
                with self.db.dbapi.execute("""
                    SELECT handle, gramps_id, json_data
                    FROM person
                    WHERE json_data::text ILIKE %s
                    LIMIT %s OFFSET %s
                """, (f'%{query}%', pagesize - len(results), 0 if results else offset)) as cur:
                    for row in cur.fetchall():
                        results.append({
                            'handle': row[0],
                            'type': 'person',
                            'gramps_id': row[1],
                            'data': row[2] if include_content else None,
                            'relevance': 1.0
                        })
        
        # Format results
        hits = []
        for i, result in enumerate(results):
            hit = self._format_hit(result, rank=offset + i, include_content=include_content)
            hits.append(hit)
        
        return len(results), hits


class SearchIndexer(PostgreSQLSearchIndexer):
    """Full-text search indexer using PostgreSQL native search."""
    
    def __init__(
        self,
        tree: str,
        db_url: Optional[str] = None,
    ):
        """Initialize the full-text indexer."""
        super().__init__(
            tree=tree, 
            db_url=db_url, 
            embedding_function=None, 
            use_fts=True,
            use_semantic_text=False
        )


class SemanticSearchIndexer(PostgreSQLSearchIndexer):
    """Semantic (vector) search indexer using pgvector."""
    
    SUFFIX = "__s"
    SUFFIX_PUBLIC = "__s__p"
    
    def __init__(
        self,
        tree: str,
        db_url: Optional[str] = None,
        embedding_function: Callable | None = None,
    ):
        """Initialize the semantic indexer."""
        super().__init__(
            tree=tree,
            db_url=db_url,
            embedding_function=embedding_function,
            use_fts=False,
            use_semantic_text=True
        )
        
        if not embedding_function:
            LOG.warning("No embedding function provided for semantic search")


# Make it a drop-in replacement
SearchIndexerBase = PostgreSQLSearchIndexer