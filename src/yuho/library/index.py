"""
Library index for Yuho statute packages.

Provides search and discovery of statute packages by section number,
title, jurisdiction, and keywords.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging

from yuho.library.package import PackageMetadata

logger = logging.getLogger(__name__)


# Default library paths
DEFAULT_LIBRARY_INDEX = Path.home() / ".yuho" / "library" / "index.json"
DEFAULT_LIBRARY_DIR = Path.home() / ".yuho" / "library" / "packages"


@dataclass
class IndexEntry:
    """An entry in the library index."""
    section_number: str
    title: str
    jurisdiction: str
    contributor: str
    version: str
    description: str
    tags: List[str]
    package_path: str  # Relative path within library
    content_hash: str
    
    @classmethod
    def from_metadata(
        cls, metadata: PackageMetadata, package_path: str, content_hash: str
    ) -> "IndexEntry":
        """Create entry from package metadata."""
        return cls(
            section_number=metadata.section_number,
            title=metadata.title,
            jurisdiction=metadata.jurisdiction,
            contributor=metadata.contributor,
            version=metadata.version,
            description=metadata.description,
            tags=metadata.tags,
            package_path=package_path,
            content_hash=content_hash,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section_number": self.section_number,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "contributor": self.contributor,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "package_path": self.package_path,
            "content_hash": self.content_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexEntry":
        """Create from dictionary."""
        return cls(
            section_number=data["section_number"],
            title=data["title"],
            jurisdiction=data["jurisdiction"],
            contributor=data["contributor"],
            version=data["version"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            package_path=data["package_path"],
            content_hash=data.get("content_hash", ""),
        )
    
    def matches(
        self,
        section: Optional[str] = None,
        keyword: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Check if entry matches search criteria."""
        if section and section.lower() not in self.section_number.lower():
            return False
        
        if jurisdiction and jurisdiction.lower() not in self.jurisdiction.lower():
            return False
        
        if keyword:
            keyword_lower = keyword.lower()
            searchable = f"{self.title} {self.description} {' '.join(self.tags)}".lower()
            if keyword_lower not in searchable:
                return False
        
        if tags:
            # Entry must have at least one of the specified tags
            entry_tags_lower = [t.lower() for t in self.tags]
            matching_tags = any(t.lower() in entry_tags_lower for t in tags)
            if not matching_tags:
                return False
        
        return True


class LibraryIndex:
    """
    Index of installed statute packages.
    
    Provides efficient lookup by section number, jurisdiction,
    and keyword search.
    """
    
    def __init__(
        self,
        index_path: Optional[Path] = None,
        library_dir: Optional[Path] = None,
    ):
        """
        Initialize the library index.
        
        Args:
            index_path: Path to index JSON file
            library_dir: Path to library directory
        """
        self.index_path = index_path or DEFAULT_LIBRARY_INDEX
        self.library_dir = library_dir or DEFAULT_LIBRARY_DIR
        self._entries: Dict[str, IndexEntry] = {}
        self._load()
    
    def _load(self) -> None:
        """Load index from disk."""
        if not self.index_path.exists():
            logger.debug(f"No index found at {self.index_path}")
            return
        
        try:
            with open(self.index_path) as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                entry = IndexEntry.from_dict(entry_data)
                self._entries[entry.section_number] = entry
            
            logger.debug(f"Loaded {len(self._entries)} index entries")
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
    
    def _save(self) -> None:
        """Save index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "entries": [e.to_dict() for e in self._entries.values()],
        }
        
        with open(self.index_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def add(self, entry: IndexEntry) -> None:
        """Add or update an entry in the index."""
        self._entries[entry.section_number] = entry
        self._save()
    
    def remove(self, section_number: str) -> bool:
        """
        Remove an entry from the index.
        
        Returns:
            True if entry was removed, False if not found
        """
        if section_number in self._entries:
            del self._entries[section_number]
            self._save()
            return True
        return False
    
    def get(self, section_number: str) -> Optional[IndexEntry]:
        """Get an entry by section number."""
        return self._entries.get(section_number)
    
    def search(
        self,
        section: Optional[str] = None,
        keyword: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[IndexEntry]:
        """
        Search the library index.
        
        Args:
            section: Section number pattern to match
            keyword: Keyword to search in title/description/tags
            jurisdiction: Jurisdiction to filter by
            tags: Tags to filter by (matches if entry has any)
            limit: Maximum results to return
            
        Returns:
            List of matching entries
        """
        results = []
        
        for entry in self._entries.values():
            if entry.matches(section, keyword, jurisdiction, tags):
                results.append(entry)
                if len(results) >= limit:
                    break
        
        # Sort by section number
        results.sort(key=lambda e: e.section_number)
        
        return results
    
    def list_all(self) -> List[IndexEntry]:
        """List all entries in the index."""
        return sorted(self._entries.values(), key=lambda e: e.section_number)
    
    def count(self) -> int:
        """Get total number of indexed packages."""
        return len(self._entries)
    
    def rebuild(self) -> int:
        """
        Rebuild index from installed packages.
        
        Returns:
            Number of packages indexed
        """
        self._entries.clear()
        
        if not self.library_dir.exists():
            return 0
        
        from yuho.library.package import Package
        
        count = 0
        for pkg_path in self.library_dir.glob("*.yhpkg"):
            try:
                pkg = Package.from_yhpkg(pkg_path)
                entry = IndexEntry.from_metadata(
                    pkg.metadata,
                    pkg_path.name,
                    pkg.content_hash(),
                )
                self._entries[entry.section_number] = entry
                count += 1
            except Exception as e:
                logger.warning(f"Failed to index {pkg_path}: {e}")
        
        self._save()
        return count


def search_library(
    section: Optional[str] = None,
    keyword: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to search the library.
    
    Args:
        section: Section number pattern
        keyword: Search keyword
        jurisdiction: Jurisdiction filter
        tags: Tags to filter by
        
    Returns:
        List of matching packages as dictionaries
    """
    index = LibraryIndex()
    results = index.search(section, keyword, jurisdiction, tags)
    return [r.to_dict() for r in results]
