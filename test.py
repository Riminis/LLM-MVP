import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

from src.pipeline import KnowledgeBasePipeline
from src.document_loader import DocumentLoader


def check_files() -> bool:
    """Verify required files exist."""
    required_files = {
        "examples/math_sample.txt": "Input file",
        "prompts/universal_prompt.txt": "Prompt",
        "certs/sber_cert.pem": "SSL Certificate",
    }

    logger.info("Checking required files...")
    for filepath, description in required_files.items():
        if Path(filepath).exists():
            logger.info(f"Found: {description}")
        else:
            logger.error(f"Missing: {description} ({filepath})")
            return False
    return True


def main():
    """Main entry point."""
    if not check_files():
        logger.error("Some required files are missing")
        sys.exit(1)

    logger.info("Initializing pipeline...")
    try:
        pipeline = KnowledgeBasePipeline(
            output_dir="vault",
            index_path=".obsidian/index.json"
        )
        logger.info("Pipeline initialized successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    input_file = "examples/math_sample.txt"
    prompt_file = "prompts/universal_prompt.txt"

    logger.info("Starting document processing")
    logger.info(f"Input: {input_file}")
    logger.info(f"Prompt: {prompt_file}")

    try:
        output_file = pipeline.process_document(
            input_file=input_file,
            prompt_file=prompt_file
        )
        logger.info("Document processed successfully")
        logger.info(f"Output: {output_file}")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    logger.info("Knowledge base statistics:")
    stats = pipeline.get_graph_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    orphaned = pipeline.find_orphaned_files()
    if orphaned:
        logger.warning("Files without links:")
        for file in orphaned:
            logger.warning(f"  {file}")
    else:
        logger.info("All files are properly connected")

    logger.info("Index saved to .obsidian/index.json")
    logger.info("Process completed")


if __name__ == "__main__":
    main()
