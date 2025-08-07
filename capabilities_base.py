"""
Gramps Capabilities Abstraction Layer

This module provides abstract base classes for advanced database capabilities
that can be implemented by different backends (PostgreSQL Enhanced, MongoDB, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from enum import Enum, auto


class CapabilityLevel(Enum):
    """Standard capability levels across all backends"""
    NONE = auto()
    BASIC = auto()       # Basic built-in features
    STANDARD = auto()    # Standard extensions enabled
    ENHANCED = auto()    # Advanced features available
    FULL = auto()        # All features enabled
    

class SearchCapabilityBase(ABC):
    """Abstract base for search capabilities"""
    
    @abstractmethod
    def search(self, 
               query: str, 
               search_type: str = 'auto',
               limit: int = 100,
               **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search with the given query.
        
        Args:
            query: Search query string
            search_type: Type of search ('auto', 'exact', 'fuzzy', 'phonetic', 'semantic')
            limit: Maximum results to return
            **kwargs: Backend-specific options
            
        Returns:
            List of search results with handle, type, and relevance
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get available search capabilities.
        
        Returns:
            Dictionary of capability names to availability
        """
        pass
    
    @abstractmethod
    def can_do(self, capability: str) -> bool:
        """Check if a specific capability is available"""
        pass


class VectorCapabilityBase(ABC):
    """Abstract base for vector/AI capabilities"""
    
    @abstractmethod
    def store_embedding(self,
                       object_handle: str,
                       embedding_type: str,
                       vector: List[float],
                       metadata: Optional[Dict] = None) -> bool:
        """Store a vector embedding for an object"""
        pass
    
    @abstractmethod
    def find_similar(self,
                    query_vector: List[float],
                    embedding_type: str,
                    limit: int = 10,
                    threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find similar objects by vector similarity"""
        pass
    
    @abstractmethod
    def find_dna_matches(self,
                        person_handle: str,
                        min_cm: float = 7.0,
                        min_snps: int = 500) -> List[Dict[str, Any]]:
        """Find DNA matches using vector similarity"""
        pass


class GraphCapabilityBase(ABC):
    """Abstract base for graph database capabilities"""
    
    @abstractmethod
    def find_relationship_path(self,
                              person1_handle: str,
                              person2_handle: str,
                              max_depth: int = 10) -> List[List[str]]:
        """Find all paths between two people"""
        pass
    
    @abstractmethod
    def find_common_ancestors(self,
                             handles: List[str],
                             max_generations: int = 20) -> List[str]:
        """Find common ancestors of multiple people"""
        pass
    
    @abstractmethod
    def calculate_relationship(self,
                              person1_handle: str,
                              person2_handle: str) -> str:
        """Calculate the exact relationship between two people"""
        pass
    
    @abstractmethod
    def detect_pedigree_collapse(self,
                                person_handle: str,
                                generations: int = 10) -> List[Dict[str, Any]]:
        """Detect where the same person appears multiple times in a pedigree"""
        pass


class AdvancedCapabilities(ABC):
    """
    Main interface for advanced database capabilities.
    Backends implement this to expose their features.
    """
    
    @abstractmethod
    def has_search_capability(self) -> bool:
        """Check if search capabilities are available"""
        pass
    
    @abstractmethod
    def get_search_api(self) -> Optional[SearchCapabilityBase]:
        """Get the search API if available"""
        pass
    
    @abstractmethod
    def has_vector_capability(self) -> bool:
        """Check if vector/AI capabilities are available"""
        pass
    
    @abstractmethod
    def get_vector_api(self) -> Optional[VectorCapabilityBase]:
        """Get the vector API if available"""
        pass
    
    @abstractmethod
    def has_graph_capability(self) -> bool:
        """Check if graph capabilities are available"""
        pass
    
    @abstractmethod
    def get_graph_api(self) -> Optional[GraphCapabilityBase]:
        """Get the graph API if available"""
        pass
    
    @abstractmethod
    def get_capability_level(self) -> CapabilityLevel:
        """Get the overall capability level"""
        pass
    
    @abstractmethod
    def get_all_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed information about all capabilities.
        
        Returns:
            Dictionary with capability information
        """
        pass