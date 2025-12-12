import os
import logging
import json
import base64
import uuid
from typing import Optional, Dict, Any
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class GigaChatClient:
    """Client for Sber GigaChat API integration."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat"
    ):
        self.client_id = client_id or os.getenv("GIGACHAT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GIGACHAT_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing GIGACHAT credentials. "
                "Set GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET in environment."
            )

        self.scope = scope
        self.model = model
        self.oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self.access_token: Optional[str] = None

        self.oauth_cert = self._find_certificate("sber_oauth_cert.pem")
        self.api_cert = self._find_certificate("sber_api_cert.pem")
        self.session = self._create_session()

    def _find_certificate(self, filename: str) -> Optional[str]:
        """Locate SSL certificate from standard paths."""
        possible_paths = [
            Path("certs") / filename,
            Path(__file__).parent.parent / "certs" / filename,
            Path.home() / ".sber_certs" / filename,
        ]

        for cert_path in possible_paths:
            if cert_path.exists():
                logger.debug(f"Certificate found: {cert_path}")
                return str(cert_path)

        logger.warning(f"Certificate not found: {filename}")
        return None

    def _create_session(self) -> requests.Session:
        """Create session with retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _handle_response_error(
        self,
        response: requests.Response,
        context: str
    ) -> None:
        """Process and log API error responses."""
        logger.error(f"{context}")
        logger.error(f"Status: {response.status_code}")

        try:
            error_data = response.json()
            logger.error(f"Response: {json.dumps(error_data, indent=2)}")
        except json.JSONDecodeError:
            logger.error(f"Text: {response.text[:500]}")

        response.raise_for_status()

    def get_token(self) -> str:
        """Retrieve OAuth token from Sber API."""
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_auth = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {encoded_auth}"
            }
            payload = {"scope": self.scope}

            logger.info("Requesting authentication token...")

            verify_param = self.oauth_cert if self.oauth_cert else False

            response = self.session.post(
                self.oauth_url,
                headers=headers,
                data=payload,
                verify=verify_param,
                timeout=10
            )

            if response.status_code != 200:
                self._handle_response_error(response, "Failed to get authentication token")

            try:
                token_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse token response: {e}")
                raise ValueError("Invalid JSON response from auth endpoint") from e

            if "access_token" not in token_data:
                logger.error(f"Missing access_token in response. Keys: {list(token_data.keys())}")
                raise KeyError("access_token not found in response")

            self.access_token = token_data["access_token"]
            logger.info("Authentication successful")
            return self.access_token

        except requests.exceptions.SSLError as e:
            logger.error(f"SSL certificate error: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def chat(
        self,
        text: str,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 20000
    ) -> str:
        """Send request to GigaChat API."""
        if not self.access_token:
            self.get_token()

        if len(text) > max_tokens:
            logger.warning(f"Text truncated from {len(text)} to {max_tokens} chars")
            text = text[:max_tokens]

        request_text = prompt + text

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": request_text}],
                "temperature": temperature
            }

            logger.info("Sending request to GigaChat API...")

            verify_param = self.api_cert if self.api_cert else False

            response = self.session.post(
                self.api_url,
                headers=headers,
                json=payload,
                verify=verify_param,
                timeout=60
            )

            if response.status_code != 200:
                self._handle_response_error(response, "API request failed")

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response: {e}")
                raise ValueError("Invalid JSON response from GigaChat API") from e

            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Unexpected response format: {e}")
                raise ValueError("Invalid response format from GigaChat") from e

            logger.info(f"Response received ({len(content)} characters)")
            return content

        except requests.exceptions.SSLError as e:
            logger.error(f"SSL certificate error during API request: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            raise

    def chat_json(
        self,
        text: str,
        prompt: str,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Get JSON response from chat."""
        raw_output = self.chat(text=text, prompt=prompt, temperature=temperature)

        try:
            import re

            json_match = re.search(
                r'```(?:json)?\s*([\s\S]*?)\s*```',
                raw_output
            )

            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = raw_output.strip()

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError("Could not parse JSON response") from e
