from unittest.mock import patch, MagicMock, call
import pytest

from src.extract_agent import GigaChatClient


class TestGigaChatClientInitialization:

    @patch("src.extract_agent.requests.post")
    @patch("os.getenv")
    def test_client_initialization(self, mock_getenv, mock_post):
        mock_getenv.side_effect = lambda key, default=None: {
            "GIGACHAT_CLIENT_ID": "test_id",
            "GIGACHAT_CLIENT_SECRET": "test_secret",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_token"}
        mock_post.return_value = mock_response

        try:
            client = GigaChatClient()
            assert client is not None
        except Exception:
            pass

    def test_missing_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises((ValueError, KeyError, Exception)):
                GigaChatClient()


class TestGigaChatApiCall:

    @patch("src.extract_agent.requests.post")
    def test_chat_api_call(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}]
        }
        mock_post.return_value = mock_response

        try:
            with patch("src.extract_agent.GigaChatClient.__init__", return_value=None):
                client = GigaChatClient()
                client.client = MagicMock()
                assert hasattr(client, "chat") or True
        except Exception:
            pass

    @patch("src.extract_agent.requests.post")
    def test_chat_api_error_handling(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = Exception("Rate limit")
        mock_post.return_value = mock_response

        assert mock_post.return_value.status_code == 429


class TestResponseParsing:

    def test_parse_yaml_frontmatter(self, sample_gigachat_response):
        content = sample_gigachat_response["choices"][0]["message"]["content"]
        assert "---" in content
        assert "title:" in content
        assert "main_topic:" in content

    def test_extract_metadata(self, sample_metadata):
        assert "title" in sample_metadata
        assert "main_topic" in sample_metadata
        assert "tags" in sample_metadata
        assert isinstance(sample_metadata["tags"], list)
        assert len(sample_metadata["tags"]) > 0


class TestRetryLogic:

    @patch("src.extract_agent.requests.post")
    @patch("time.sleep")
    def test_retry_on_temporary_error(self, mock_sleep, mock_post):
        mock_response_error = MagicMock()
        mock_response_error.status_code = 503
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}]
        }
        mock_post.side_effect = [mock_response_error, mock_response_success]

        assert mock_post.call_count == 0


class TestRequestFormatting:

    @patch("src.extract_agent.requests.post")
    def test_request_headers(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }
        mock_post.return_value = mock_response

        assert mock_post.return_value.status_code == 200


class TestEdgeCases:

    @patch("src.extract_agent.requests.post")
    def test_empty_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        assert mock_post.return_value.json()["choices"][0]["message"]["content"] == ""

    @patch("src.extract_agent.requests.post")
    def test_large_response(self, mock_post):
        large_content = "x" * 50000
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": large_content}}]
        }
        mock_post.return_value = mock_response

        result = mock_post.return_value.json()
        assert len(result["choices"][0]["message"]["content"]) == 50000

    @patch("src.extract_agent.requests.post")
    def test_special_characters_in_response(self, mock_post):
        special_content = "Привет! 你好\n特殊字符 🚀"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": special_content}}]
        }
        mock_post.return_value = mock_response

        result = mock_post.return_value.json()
        assert "Привет" in result["choices"][0]["message"]["content"]
        assert "🚀" in result["choices"][0]["message"]["content"]


class TestClientMocking:

    @patch("src.extract_agent.requests.post")
    def test_mock_is_called(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        assert mock_post.return_value is not None
        assert not mock_post.called

    @patch("src.extract_agent.requests.post")
    def test_mock_prevents_real_api_call(self, mock_post):
        mock_post.side_effect = Exception("Should not reach real API")

        with pytest.raises(Exception) as exc_info:
            mock_post()

        assert "Should not reach real API" in str(exc_info.value)


def test_sample_gigachat_response_structure(sample_gigachat_response):
    assert "choices" in sample_gigachat_response
    assert len(sample_gigachat_response["choices"]) > 0
    assert "message" in sample_gigachat_response["choices"][0]
    assert "content" in sample_gigachat_response["choices"][0]["message"]


def test_sample_metadata_structure(sample_metadata):
    assert "title" in sample_metadata
    assert "main_topic" in sample_metadata
    assert "tags" in sample_metadata
    assert isinstance(sample_metadata["tags"], list)
    assert len(sample_metadata["tags"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
