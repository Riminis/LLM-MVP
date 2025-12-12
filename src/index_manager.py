import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IndexManager:
    """Manage knowledge base index for file relationships and metadata."""

    def __init__(self, index_path: str = ".obsidian/index.json"):
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(exist_ok=True)
        self.data = self._load_or_create_index()

    def _load_or_create_index(self) -> Dict:
        """Load existing index or create new one."""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "backlinks" not in data:
                data["backlinks"] = {}

            return data

        return {
            "version": 1,
            "last_updated": datetime.now().isoformat(),
            "stats": {"total_files": 0, "total_links": 0},
            "files": {},
            "topics_index": {},
            "tags_index": {},
            "backlinks": {}
        }

    def save(self):
        """Save index to disk."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        logger.info(f"Index saved to {self.index_path}")

    def add_file(
        self,
        filename: str,
        title: str,
        tags: List[str],
        topics: List[str],
        parent: Optional[str] = None,
        related: Optional[List[str]] = None
    ):
        """Add file to index."""
        self.data["files"][filename] = {
            "title": title,
            "tags": tags,
            "topics": topics,
            "created": datetime.now().date().isoformat(),
            "updated": datetime.now().date().isoformat(),
            "size_chars": 0,
            "parent": parent,
            "related": related or []
        }

        self._update_topics_index(filename, topics)
        self._update_tags_index(filename, tags)
        self._update_stats()

        logger.info(f"File added: {filename}")

    def _update_topics_index(self, filename: str, topics: List[str]):
        """Update topic index."""
        for topic in topics:
            if topic not in self.data["topics_index"]:
                self.data["topics_index"][topic] = []
            if filename not in self.data["topics_index"][topic]:
                self.data["topics_index"][topic].append(filename)

    def _update_tags_index(self, filename: str, tags: List[str]):
        """Update tag index."""
        for tag in tags:
            if tag not in self.data["tags_index"]:
                self.data["tags_index"][tag] = []
            if filename not in self.data["tags_index"][tag]:
                self.data["tags_index"][tag].append(filename)

    def find_related_files(
        self,
        filename: str,
        max_results: int = 5,
        min_relevance: float = 0.3
    ) -> List[tuple]:
        """Find related files using Jaccard similarity."""
        if filename not in self.data["files"]:
            return []

        current_file = self.data["files"][filename]
        current_tags = set(current_file["tags"])
        current_topics = set(current_file["topics"])

        related = {}

        for other_filename, file_info in self.data["files"].items():
            if other_filename == filename:
                continue

            other_tags = set(file_info["tags"])
            other_topics = set(file_info["topics"])

            tags_jaccard = (
                len(current_tags & other_tags) / len(current_tags | other_tags)
                if (current_tags or other_tags) else 0
            )

            topics_jaccard = (
                len(current_topics & other_topics) / len(current_topics | other_topics)
                if (current_topics or other_topics) else 0
            )

            relevance = tags_jaccard * 0.6 + topics_jaccard * 0.4

            if relevance >= min_relevance:
                related[other_filename] = relevance

        sorted_related = sorted(
            related.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_related[:max_results]

    def find_by_tag(self, tag: str) -> List[str]:
        """Find all files with given tag."""
        return self.data["tags_index"].get(tag, [])

    def find_by_topic(self, topic: str) -> List[str]:
        """Find all files by topic."""
        return self.data["topics_index"].get(topic, [])

    def get_file_info(self, filename: str) -> Optional[Dict]:
        """Get file metadata."""
        return self.data["files"].get(filename)

    def update_related_links(self, filename: str, related: List[str]):
        """Update related file links."""
        if filename in self.data["files"]:
            self.data["files"][filename]["related"] = related
            logger.info(f"Links updated for {filename}")

    def update_backlinks(self, source: str, target: str):
        """Update backlinks (reverse links)."""
        if "backlinks" not in self.data:
            self.data["backlinks"] = {}

        if target not in self.data["backlinks"]:
            self.data["backlinks"][target] = []
        if source not in self.data["backlinks"][target]:
            self.data["backlinks"][target].append(source)

    def get_backlinks(self, filename: str) -> List[str]:
        """Get files that link to given file."""
        if "backlinks" not in self.data:
            self.data["backlinks"] = {}

        return self.data["backlinks"].get(filename, [])

    def _update_stats(self):
        """Update index statistics."""
        self.data["stats"]["total_files"] = len(self.data["files"])
        total_links = sum(
            len(info.get("related", []))
            for info in self.data["files"].values()
        )
        self.data["stats"]["total_links"] = total_links

    def export_graph_format(self) -> Dict:
        """Export graph for visualization."""
        nodes = [
            {
                "id": filename,
                "label": info["title"],
                "tags": info["tags"],
                "group": info["tags"][0] if info["tags"] else "other"
            }
            for filename, info in self.data["files"].items()
        ]

        links = []
        for filename, info in self.data["files"].items():
            for related in info.get("related", []):
                links.append({
                    "source": filename,
                    "target": related,
                    "weight": 1
                })

        return {
            "nodes": nodes,
            "links": links,
            "stats": self.data["stats"]
        }
