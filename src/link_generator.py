import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class LinkGenerator:
    """Automatically generate links between related files."""

    def __init__(self, index_manager):
        self.index = index_manager

    def extract_mentions(self, content: str) -> List[str]:
        """Extract key concepts from bold text."""
        concepts = re.findall(r'\*\*([^*]+)\*\*', content)
        return [c.lower() for c in concepts]

    def find_link_opportunities(
        self,
        filename: str,
        content: str,
        min_relevance: float = 0.4
    ) -> List[Tuple[str, str, float]]:
        """Find places where links should be added."""
        opportunities = []

        mentions = self.extract_mentions(content)

        for mention in mentions:
            for topic, files in self.index.data["topics_index"].items():
                if mention in topic or topic in mention:
                    for target_file in files:
                        if target_file != filename:
                            opportunities.append((target_file, mention, 0.8))

        related_files = self.index.find_related_files(filename)
        for target_file, relevance in related_files:
            opportunities.append((target_file, None, relevance))

        return opportunities

    def generate_links_in_content(
        self,
        filename: str,
        content: str,
        auto_link_min_confidence: float = 0.6
    ) -> str:
        """Add wiki-style links to content."""
        opportunities = self.find_link_opportunities(filename, content)

        modified_content = content
        added_links = []

        for target_file, anchor_text, confidence in opportunities:
            if confidence >= auto_link_min_confidence and anchor_text:
                anchor_without_ext = target_file.replace(".md", "")
                pattern = rf'\*\*{re.escape(anchor_text)}\*\*'

                replacement = f'[[{anchor_without_ext}|{anchor_text}]]'

                if re.search(pattern, modified_content):
                    modified_content = re.sub(
                        pattern,
                        replacement,
                        modified_content,
                        count=1
                    )
                    added_links.append(target_file)

        if added_links or len(opportunities) > 0:
            modified_content = self._add_related_section(
                modified_content,
                filename,
                opportunities
            )

        return modified_content

    def _add_related_section(
        self,
        content: str,
        filename: str,
        opportunities: List[Tuple[str, str, float]]
    ) -> str:
        """Add related topics section."""
        related_section = "\n## Related Topics\n"

        seen = set()
        for target_file, anchor_text, confidence in opportunities:
            if target_file not in seen and confidence > 0.4:
                target_name = target_file.replace(".md", "")
                target_info = self.index.get_file_info(target_file)
                target_title = (
                    target_info.get("title", target_name)
                    if target_info else target_name
                )
                related_section += f"- [[{target_name}]] - {target_title}\n"
                seen.add(target_file)

        if "## Related Topics" in content:
            content = re.sub(
                r'## Related Topics\n.*?(?=\n##|\Z)',
                related_section,
                content,
                flags=re.DOTALL
            )
        else:
            content += related_section

        return content
