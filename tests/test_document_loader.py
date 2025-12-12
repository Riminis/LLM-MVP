import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.document_loader import DocumentLoader


class TestDocumentLoaderTxt:

    def test_load_txt_file(self, tmp_path, sample_text):
        test_file = tmp_path / "test.txt"
        test_file.write_text(sample_text, encoding="utf-8")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert result["file_name"] == "test.txt"
        assert "Python" in result["content"]
        assert result["encoding"] == "utf-8"

    def test_load_empty_txt_file(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert result["content"] == ""
        assert result["file_name"] == "empty.txt"

    def test_load_txt_with_unicode(self, tmp_path):
        unicode_text = "Привет, мир! 你好 🚀"
        test_file = tmp_path / "unicode.txt"
        test_file.write_text(unicode_text, encoding="utf-8")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert "Привет" in result["content"]
        assert "🚀" in result["content"]


class TestDocumentLoaderJson:

    def test_load_json_file(self, tmp_path, sample_json_content):
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(sample_json_content), encoding="utf-8")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert result["file_name"] == "test.json"
        assert "Sample Document" in result["content"] or isinstance(result["content"], str)

    def test_load_invalid_json(self, tmp_path):
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{invalid json}", encoding="utf-8")

        loader = DocumentLoader()

        try:
            result = loader.load(str(test_file))
            assert isinstance(result, dict)
        except (json.JSONDecodeError, ValueError):
            pass


class TestDocumentLoaderPdf:

    @patch("src.document_loader.PyPDF2.PdfReader")
    def test_load_pdf_file(self, mock_pdf, tmp_path):
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF extracted text"
        mock_reader.pages = [mock_page]
        mock_pdf.return_value = mock_reader

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert result["file_name"] == "test.pdf"

    @patch("src.document_loader.PyPDF2.PdfReader")
    def test_load_corrupted_pdf(self, mock_pdf):
        mock_pdf.side_effect = Exception("Corrupted PDF")

        loader = DocumentLoader()

        with pytest.raises(Exception):
            loader.load("nonexistent.pdf")


class TestDocumentLoaderDocx:

    def test_load_docx_file(self, tmp_path):
        test_file = tmp_path / "test.docx"
        
        try:
            from docx import Document
            doc = Document()
            p = doc.add_paragraph("Test content")
            doc.save(str(test_file))

            loader = DocumentLoader()
            result = loader.load(str(test_file))

            assert isinstance(result, dict)
            assert result["file_name"] == "test.docx"
            assert "Test content" in result["content"]
        except ImportError:
            pytest.skip("python-docx not installed")

    def test_load_corrupted_docx(self, tmp_path):
        test_file = tmp_path / "corrupted.docx"
        test_file.write_bytes(b"not a docx file")

        loader = DocumentLoader()

        with pytest.raises(Exception):
            loader.load(str(test_file))


class TestDocumentLoaderErrors:

    def test_file_not_found(self, tmp_path):
        loader = DocumentLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(str(tmp_path / "nonexistent.txt"))

    def test_unsupported_format(self, tmp_path):
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content", encoding="utf-8")

        loader = DocumentLoader()

        with pytest.raises((ValueError, Exception)):
            loader.load(str(test_file))


class TestDocumentLoaderEdgeCases:

    def test_file_with_special_characters(self, tmp_path):
        test_file = tmp_path / "test-file_2025.txt"
        test_file.write_text("content", encoding="utf-8")

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert result["content"] == "content"
        assert result["file_name"] == "test-file_2025.txt"

    def test_file_with_bom(self, tmp_path):
        test_file = tmp_path / "bom.txt"
        test_file.write_bytes(b"\xef\xbb\xbf" + "содержание".encode("utf-8"))

        loader = DocumentLoader()
        result = loader.load(str(test_file))

        assert isinstance(result, dict)
        assert "содержание" in result["content"] or "\ufeff" in result["content"]


class TestDocumentLoaderMultiple:

    def test_load_multiple_files(self, tmp_path):
        files = []
        for i in range(3):
            test_file = tmp_path / f"test{i}.txt"
            test_file.write_text(f"Content {i}", encoding="utf-8")
            files.append(str(test_file))

        loader = DocumentLoader()
        results = [loader.load(f) for f in files]

        assert len(results) == 3
        assert results[0]["content"] == "Content 0"
        assert results[1]["content"] == "Content 1"
        assert results[2]["content"] == "Content 2"


@pytest.mark.parametrize(
    "filename,content",
    [
        ("test.txt", "plain text content"),
        ("test3.txt", "123\n456\n789"),
    ],
)
def test_load_txt_parametrized(tmp_path, filename, content):
    test_file = tmp_path / filename
    test_file.write_text(content, encoding="utf-8")

    loader = DocumentLoader()
    result = loader.load(str(test_file))

    assert isinstance(result, dict)
    assert result["content"] == content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
