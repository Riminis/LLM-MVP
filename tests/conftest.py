"""
tests/conftest.py - Pytest конфигурация и общие fixtures для всех тестов.

Все мокирования и настройки здесь, чтобы не повторять в каждом тесте.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_text():
    """Образец текста для тестирования."""
    return """# Основы Python

Python - это язык программирования.
Он очень популярен в data science.

## Основные концепции
- Переменные
- Функции
- Классы
"""


@pytest.fixture
def sample_json_content():
    """Образец JSON контента."""
    return {
        "title": "Sample Document",
        "content": "This is a sample document for testing.",
        "tags": ["test", "sample", "json"],
    }


@pytest.fixture
def sample_metadata():
    """Образец метаданных документа."""
    return {
        "title": "Mathematical Fundamentals",
        "main_topic": "analysis",
        "tags": ["math", "calculus", "definitions"],
        "date": "2025-12-12",
        "summary": "Ключевые определения анализа",
    }


@pytest.fixture
def sample_gigachat_response():
    """Мокированный ответ от GigaChat API."""
    return {
        "choices": [
            {
                "message": {
                    "content": """---
title: "Математический анализ: основные понятия"
main_topic: "analysis"
tags: [math, calculus, definitions]
date: "2025-12-12"
summary: "Ключевые определения анализа"
---

# Основное содержание

## Определения
- Предел функции
- Производная
- Интеграл
"""
                }
            }
        ]
    }


@pytest.fixture
def sample_index():
    """Образец индекса (как в .obsidian/index.json)."""
    return {
        "files": [
            {
                "id": 1,
                "name": "analysis-mathematical-fundamentals.md",
                "title": "Математический анализ",
                "main_topic": "analysis",
                "tags": ["math", "calculus"],
            },
            {
                "id": 2,
                "name": "algebra-basics.md",
                "title": "Основы алгебры",
                "main_topic": "algebra",
                "tags": ["math", "algebra"],
            },
        ],
        "links": [
            {"source": 1, "target": 2, "weight": 0.7},
        ],
    }


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Создаёт временную структуру проекта."""
    (tmp_path / "examples").mkdir()
    (tmp_path / "vault").mkdir()
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "prompts").mkdir()

    (tmp_path / "examples" / "sample.txt").write_text("This is a test document.")

    (tmp_path / "prompts" / "universal_prompt.txt").write_text(
        "Process: {SOURCE_CONTENT}"
    )

    return tmp_path


@pytest.fixture
def mock_requests():
    """Мокирует requests.post для GigaChat API."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """---
title: "Test Document"
main_topic: "test"
tags: [test, sample]
---

# Test Content"""
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_gigachat_client(mock_requests):
    """Мокированный GigaChatClient."""
    from src.extract_agent import GigaChatClient

    with patch.object(
        GigaChatClient, "get_token", return_value="mock_token"
    ) as mock_token:
        client = GigaChatClient()
        yield client


@pytest.fixture
def mock_pdf_loader():
    """Мокирует PyPDF2 для загрузки PDF."""
    with patch("src.document_loader.PyPDF2") as mock_pdf:
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF extracted text"
        mock_reader.pages = [mock_page]

        mock_pdf.PdfReader.return_value = mock_reader
        yield mock_pdf


@pytest.fixture
def mock_docx_loader():
    """Мокирует python-docx для загрузки DOCX."""
    with patch("src.document_loader.Document") as mock_doc:
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Docx paragraph text"

        mock_document = MagicMock()
        mock_document.paragraphs = [mock_paragraph]

        mock_doc.return_value = mock_document
        yield mock_doc


@pytest.fixture(
    params=[
        ("test.txt", "text/plain"),
        ("test.json", "application/json"),
        ("test.md", "text/markdown"),
    ]
)
def file_types(request):
    """Параметризованный fixture для разных типов файлов."""
    return request.param


@pytest.fixture(params=[0.5, 0.6, 0.7, 0.8, 0.9])
def similarity_thresholds(request):
    """Параметризованный fixture для порогов похожести."""
    return request.param


@pytest.fixture(autouse=True)
def reset_logging():
    """Сбрасывает логирование перед каждым тестом."""
    import logging

    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    yield

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def clean_env_vars(monkeypatch):
    """Очищает переменные окружения перед каждым тестом."""
    monkeypatch.delenv("GIGACHAT_CLIENT_ID", raising=False)
    monkeypatch.delenv("GIGACHAT_CLIENT_SECRET", raising=False)

    monkeypatch.setenv("GIGACHAT_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("GIGACHAT_CLIENT_SECRET", "test_client_secret")


def pytest_configure(config):
    """Конфигурация pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (requires API calls)"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Модифицирует собранные тесты."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


class AssertFileExists:
    """Проверяет что файл существует и содержит ожидаемый текст."""

    def __init__(self, path, expected_content=None):
        self.path = Path(path)
        self.expected_content = expected_content

    def __enter__(self):
        assert self.path.exists(), f"File {self.path} does not exist"
        return self

    def __exit__(self, *args):
        pass

    def contains(self, text):
        """Проверяет что файл содержит текст."""
        content = self.path.read_text()
        assert text in content, f"'{text}' not found in {self.path}"


@pytest.fixture
def assert_file_exists():
    """Fixture для проверки файлов."""
    return AssertFileExists


import time


@pytest.fixture
def timer():
    """Простой timer для измерения времени выполнения."""

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, *args):
            self.end_time = time.time()

        @property
        def elapsed(self):
            return self.end_time - self.start_time

    return Timer()


@pytest.fixture
def assert_raises_with_message():
    """Проверяет что исключение содержит ожидаемое сообщение."""

    def _assert_raises(exception_type, message_substr, callable_obj, *args, **kwargs):
        try:
            callable_obj(*args, **kwargs)
            assert False, f"Expected {exception_type} was not raised"
        except exception_type as e:
            assert (
                message_substr in str(e)
            ), f"Expected '{message_substr}' in '{str(e)}'"

    return _assert_raises


import logging
from io import StringIO


@pytest.fixture
def captured_logs():
    """Захватывает логи для проверки в тестах."""

    class LogCapture:
        def __init__(self):
            self.handler = None
            self.stream = StringIO()
            self.records = []

        def __enter__(self):
            self.handler = logging.StreamHandler(self.stream)
            self.handler.setLevel(logging.DEBUG)
            logger = logging.getLogger()
            logger.addHandler(self.handler)
            logger.setLevel(logging.DEBUG)
            return self

        def __exit__(self, *args):
            logger = logging.getLogger()
            logger.removeHandler(self.handler)

        @property
        def text(self):
            return self.stream.getvalue()

        def has_message(self, message):
            return message in self.text

    return LogCapture()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Добавляет дополнительную информацию в конце запуска тестов."""
    if exitstatus == 0:
        terminalreporter.section("All tests passed!", sep="=")
        terminalreporter.write_line(
            "Совет: запустите с --cov для проверки покрытия кода\n"
        )
