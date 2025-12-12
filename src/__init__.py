from src.extract_agent import GigaChatClient
from src.document_loader import DocumentLoader
from src.index_manager import IndexManager
from src.link_generator import LinkGenerator
from src.pipeline import KnowledgeBasePipeline

__version__ = "1.0.0"
__all__ = [
    "GigaChatClient",
    "DocumentLoader",
    "IndexManager",
    "LinkGenerator",
    "KnowledgeBasePipeline"
]
