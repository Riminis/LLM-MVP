"""
tests/__init__.py

Инициализация пакета tests.
"""

__version__ = "1.0.0"

from pathlib import Path

TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"
UNIT_TESTS_DIR = TEST_DIR / "unit"
INTEGRATION_TESTS_DIR = TEST_DIR / "integration"

__all__ = [
    "TEST_DIR",
    "FIXTURES_DIR",
    "UNIT_TESTS_DIR",
    "INTEGRATION_TESTS_DIR",
]
