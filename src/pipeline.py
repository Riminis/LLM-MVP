import json
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

from src.extract_agent import GigaChatClient
from src.document_loader import DocumentLoader
from src.index_manager import IndexManager
from src.link_generator import LinkGenerator

logger = logging.getLogger(__name__)


class KnowledgeBasePipeline:
    """Process documents and manage knowledge base."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        output_dir: str = "vault",
        index_path: str = ".obsidian/index.json"
    ):
        self.client = GigaChatClient(client_id, client_secret)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.index = IndexManager(index_path)
        self.link_generator = LinkGenerator(self.index)

    def process_document(
        self,
        input_file: str,
        prompt_file: str,
        output_filename: Optional[str] = None
    ) -> str:
        """Process document and add to knowledge base."""
        logger.info(f"Processing: {input_file}")

        doc_data = DocumentLoader.load(input_file)
        text = doc_data['content']
        original_filename = doc_data['file_name']
        original_size = len(text)

        prompt_data = DocumentLoader.load(prompt_file)
        prompt = prompt_data['content']

        logger.info(f"Text size: {len(text)} characters")
        logger.info("Processing with GigaChat...")

        raw_output = self.client.chat(text=text, prompt=prompt)

        frontmatter, content = self._parse_response(raw_output)

        if "main_topic" in frontmatter and frontmatter["main_topic"]:
            main_topic = frontmatter["main_topic"].lower().strip()
            title = frontmatter.get("title", "").lower().strip()
            filename = self._create_filename_from_topic(main_topic, title)
        else:
            filename = output_filename or self._sanitize_filename(
                frontmatter.get("title", original_filename)
            )

        filename = filename + ".md" if not filename.endswith(".md") else filename

        title = frontmatter.get("title", filename.replace(".md", ""))
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        topics = self._extract_topics(content)

        self.index.add_file(
            filename=filename,
            title=title,
            tags=tags,
            topics=topics
        )

        content = self.link_generator.generate_links_in_content(
            filename,
            content,
            auto_link_min_confidence=0.6
        )

        related_files = self.index.find_related_files(filename)

        output_path = self.output_dir / filename
        self._save_markdown_file(
            output_path,
            frontmatter,
            content
        )

        self.index.save()

        logger.info(f"File saved: {output_path}")

        return str(output_path)

    def _create_filename_from_topic(self, main_topic: str, title: str) -> str:
        """Create filename from main topic and title."""
        topic_clean = self._sanitize_filename(main_topic)
        title_words = title.split()
        title_clean = self._sanitize_filename(title)

        if title_clean and title_clean != topic_clean:
            key_words = [
                w for w in title_words
                if len(w) > 3 and w not in main_topic
            ][:2]
            if key_words:
                suffix = '-'.join(
                    self._sanitize_filename(w) for w in key_words
                )
                return f"{topic_clean}-{suffix}"

        return topic_clean

    def _parse_response(self, raw_output: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter and content with robust error handling."""
        raw_output = raw_output.strip()

        if raw_output.startswith("```markdown"):
            raw_output = raw_output[len("```markdown"):].strip()
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3].strip()

        frontmatter_match = re.match(
            r'^---\n(.*?)\n---\n(.*)$',
            raw_output,
            re.DOTALL
        )

        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            content = frontmatter_match.group(2)

            try:
                import yaml
                frontmatter = yaml.safe_load(frontmatter_text) or {}
            except Exception as e:
                logger.warning(f"YAML parsing failed: {e}. Using fallback parsing.")
                frontmatter = self._parse_frontmatter_fallback(frontmatter_text)
        else:
            logger.warning("YAML frontmatter not found. Attempting extraction...")
            frontmatter, content = self._extract_frontmatter_from_content(raw_output)

        return frontmatter, content

    def _extract_frontmatter_from_content(self, content: str) -> Tuple[Dict, str]:
        """Extract frontmatter from content if not properly formatted."""
        frontmatter = {}

        lines = content.split('\n')
        content_start = 0

        for i, line in enumerate(lines):
            if ':' in line and not line.startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key in ['title', 'main_topic', 'date', 'summary']:
                        value = value.strip('"\'')
                        if key == 'title':
                            frontmatter['title'] = value
                        elif key == 'main_topic':
                            frontmatter['main_topic'] = value
                        elif key == 'date':
                            frontmatter['date'] = value
                        elif key == 'summary':
                            frontmatter['summary'] = value
                        content_start = i + 1
                    elif key == 'tags':
                        if value.startswith('[') and value.endswith(']'):
                            items = [
                                item.strip().strip('"\'')
                                for item in value[1:-1].split(',')
                            ]
                            frontmatter['tags'] = items
                        else:
                            frontmatter['tags'] = [value.strip('"\'')]
                        content_start = i + 1
                except ValueError:
                    break
            elif line.startswith('#'):
                break

        if frontmatter:
            content = '\n'.join(lines[content_start:]).strip()
            logger.info("Frontmatter extracted from content")
        else:
            frontmatter = {
                'title': 'Untitled',
                'tags': [],
                'main_topic': 'general'
            }

        return frontmatter, content

    def _parse_frontmatter_fallback(self, frontmatter_text: str) -> Dict:
        """Fallback parser for malformed YAML."""
        frontmatter = {}

        lines = frontmatter_text.strip().split('\n')

        for line in lines:
            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            value = value.strip('"\'')

            if value.startswith('[') and value.endswith(']'):
                try:
                    items = [
                        item.strip().strip('"\'')
                        for item in value[1:-1].split(',')
                    ]
                    frontmatter[key] = items
                except Exception:
                    frontmatter[key] = value
            elif value.lower() in ('true', 'false'):
                frontmatter[key] = value.lower() == 'true'
            elif value.isdigit():
                frontmatter[key] = int(value)
            else:
                frontmatter[key] = value

        return frontmatter

    def _extract_topics(self, content: str) -> list:
        """Extract topics from content headings."""
        headings = re.findall(r'^## (.+)$', content, re.MULTILINE)
        topics = [h.lower().replace(" ", "_") for h in headings[:5]]
        return topics

    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename."""
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename.lower().strip('-')

    def _save_markdown_file(
        self,
        filepath: Path,
        frontmatter: dict,
        content: str
    ):
        """Save markdown file with frontmatter."""
        try:
            import yaml
            yaml_available = True
        except ImportError:
            yaml_available = False
            logger.warning("PyYAML not installed, saving without YAML")

        if yaml_available:
            yaml_str = yaml.dump(
                frontmatter,
                default_flow_style=False,
                allow_unicode=True
            )
            final_content = f"---\n{yaml_str}---\n\n{content}"
        else:
            final_content = f"---\n{self._dict_to_yaml_string(frontmatter)}---\n\n{content}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)

    def _dict_to_yaml_string(self, data: dict) -> str:
        """Convert dict to YAML string without yaml library."""
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            elif isinstance(value, str):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
        return '\n'.join(lines) + '\n'

    def get_graph_stats(self) -> dict:
        """Get knowledge base statistics."""
        return {
            **self.index.data["stats"],
            "unique_topics": len(self.index.data["topics_index"]),
            "unique_tags": len(self.index.data["tags_index"])
        }

    def find_orphaned_files(self) -> list:
        """Find files without links."""
        orphaned = []
        for filename, info in self.index.data["files"].items():
            incoming = len(self.index.get_backlinks(filename))
            outgoing = len(info.get("related", []))
            if incoming == 0 and outgoing == 0:
                orphaned.append(filename)
        return orphaned
